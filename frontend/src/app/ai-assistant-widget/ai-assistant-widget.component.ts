/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core'
import { FormsModule } from '@angular/forms'
import { NgClass } from '@angular/common'
import { MatButtonModule } from '@angular/material/button'
import { MatCardModule } from '@angular/material/card'
import { MatFormFieldModule } from '@angular/material/form-field'
import { MatIconModule } from '@angular/material/icon'
import { MatInputModule } from '@angular/material/input'
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner'
import { AiAssistantService } from '../Services/ai-assistant.service'
import { firstValueFrom } from 'rxjs'

type ChatLine = {
  role: 'assistant' | 'user'
  content: string
}

@Component({
  standalone: true,
  selector: 'app-ai-assistant-widget',
  templateUrl: './ai-assistant-widget.component.html',
  styleUrls: ['./ai-assistant-widget.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgClass,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule
  ]
})
export class AiAssistantWidgetComponent {
  private readonly assistantService = inject(AiAssistantService)

  isOpen = signal(false)
  isLoading = signal(false)
  input = signal('')
  messages = signal<ChatLine[]>([
    {
      role: 'assistant',
      content: 'Ask me about product details, pricing, or anything inside Juice Shop.'
    }
  ])

  suggestedQuestions = [
    'What does the app expose about product pricing?',
    'How does the checkout flow work?',
    'What security-sensitive features are in the app?'
  ]

  toggleWidget () {
    this.isOpen.update(prev => !prev)
  }

  applySuggestion (question: string) {
    this.input.set(question)
  }

  async sendMessage () {
    const message = this.input().trim()
    if (!message || this.isLoading()) return

    this.messages.update(prev => [...prev, { role: 'user', content: message }])
    this.input.set('')
    this.isLoading.set(true)

    try {
      const response = await firstValueFrom(this.assistantService.sendMessage(message))
      const answer = response?.answer || 'I could not get a response from the assistant.'
      const sourceSuffix = response?.sources?.length ? `\n\nSources: ${response.sources.join(', ')}` : ''
      this.messages.update(prev => [...prev, { role: 'assistant', content: answer + sourceSuffix }])
    } catch {
      this.messages.update(prev => [...prev, { role: 'assistant', content: 'The assistant service is unavailable right now.' }])
    } finally {
      this.isLoading.set(false)
    }
  }
}
