export type Role = 'user' | 'assistant'

export interface Message {
    text: string
    actor: Role
}