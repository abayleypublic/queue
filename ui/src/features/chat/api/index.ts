import Config from "@/config"
import { type Message } from '@/features/chat/types'

interface GetChatArgs {
    id: string
}

export const GetChat = async ({ id }: GetChatArgs): Promise<Array<Message>> => {
    const response = await fetch(`${Config.apiURL}/service/messages/${id}`)
    if (response.status === 404) {
        return []
    }
    return await response.json()
}

interface SendMessageArgs {
    id: string
    message: string
}

export const SendMessage = async ({ id, message }: SendMessageArgs): Promise<void> => {
    await fetch(`${Config.apiURL}/service/messages/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: message
        })
    })
}