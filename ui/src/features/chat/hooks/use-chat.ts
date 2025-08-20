import useSWR from 'swr'

import { GetChat, SendMessage } from '@/features/chat/api'
import type { Role } from '@/features/chat/types'

interface useChatArgs {
    id: string
}

const useChat = ({ id }: useChatArgs) => {
    const { data, mutate, ...rest } = useSWR(({ id }), GetChat)

    const send = async (message: string) => {
        const messages = [...(data || []), { actor: 'user' as Role, text: message }]

        mutate(async () => {
            await SendMessage({ id, message })
            return messages
        }, {
            optimisticData: messages,
        })
    }

    return { data, send, ...rest }
}

export default useChat