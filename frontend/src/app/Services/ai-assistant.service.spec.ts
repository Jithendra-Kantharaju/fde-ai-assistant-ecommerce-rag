/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing'
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http'
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing'
import { AiAssistantService } from './ai-assistant.service'

describe('AiAssistantService', () => {
  let service: AiAssistantService
  let httpMock: HttpTestingController

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
    })
    service = TestBed.inject(AiAssistantService)
    httpMock = TestBed.inject(HttpTestingController)
  })

  afterEach(() => {
    httpMock.verify()
  })

  it('should post messages to the assistant endpoint', () => {
    service.sendMessage('What is the pricing?').subscribe(response => {
      expect(response.answer).toBe('ok')
      expect(response.sources).toEqual(['README.md'])
    })

    const request = httpMock.expectOne('http://localhost:8001/assistant/chat')
    expect(request.request.method).toBe('POST')
    expect(request.request.body).toEqual({ message: 'What is the pricing?' })
    request.flush({ answer: 'ok', sources: ['README.md'], retrieved_chunks: 1, model: 'gpt-4.1-mini' })
  })
})
