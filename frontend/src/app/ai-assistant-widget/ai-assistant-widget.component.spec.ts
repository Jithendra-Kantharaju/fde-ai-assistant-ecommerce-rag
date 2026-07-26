/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { ComponentFixture, TestBed } from '@angular/core/testing'
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http'
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing'
import { AiAssistantWidgetComponent } from './ai-assistant-widget.component'

describe('AiAssistantWidgetComponent', () => {
  let fixture: ComponentFixture<AiAssistantWidgetComponent>
  let httpMock: HttpTestingController

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiAssistantWidgetComponent],
      providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
    }).compileComponents()

    fixture = TestBed.createComponent(AiAssistantWidgetComponent)
    httpMock = TestBed.inject(HttpTestingController)
    fixture.detectChanges()
  })

  afterEach(() => {
    httpMock.verify()
  })

  it('should render a floating launcher', () => {
    expect(fixture.nativeElement.querySelector('.ai-widget-launcher')).toBeTruthy()
  })

  it('should open the panel and send a question', async () => {
    fixture.componentInstance.toggleWidget()
    fixture.detectChanges()

    const textarea: HTMLTextAreaElement = fixture.nativeElement.querySelector('textarea')
    textarea.value = 'Tell me about pricing'
    textarea.dispatchEvent(new Event('input'))
    fixture.componentInstance.input.set('Tell me about pricing')

    const pending = fixture.componentInstance.sendMessage()

    const request = httpMock.expectOne('http://localhost:8001/assistant/chat')
    request.flush({ answer: 'Pricing is internal', sources: ['README.md'], retrieved_chunks: 1, model: 'gpt-4.1-mini' })

    await pending

    fixture.detectChanges()
    expect(fixture.nativeElement.textContent).toContain('Pricing is internal')
  })
})
