/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject } from '@angular/core'
import { HttpClient } from '@angular/common/http'
import { environment } from '../../environments/environment'

export interface AssistantChatRequest {
  message: string
}

export interface AssistantChatResponse {
  answer: string
  sources: string[]
  retrieved_chunks: number
  model: string
}

@Injectable({
  providedIn: 'root'
})
export class AiAssistantService {
  private readonly http = inject(HttpClient)
  private readonly assistantApiServer = environment.assistantApiServer || ''
  private readonly chatUrl = this.assistantApiServer + '/assistant/chat'

  sendMessage (message: string) {
    return this.http.post<AssistantChatResponse>(this.chatUrl, { message } satisfies AssistantChatRequest)
  }
}
