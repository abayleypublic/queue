import { toast } from 'sonner'
import useSWR from 'swr'

import { GetChat, SendMessage } from '@/features/chat/api'
import type { Role } from '@/features/chat/types'

interface useChatArgs {
    id: string
}

const useChat = ({ id }: useChatArgs) => {
    const { data, mutate, ...rest } = useSWR(({ id }), GetChat)

    const send = async (message: string, queue: string) => {
        const messages = [...(data || []), { actor: 'user' as Role, text: message }]

        mutate(async () => {
            try {
                const response = await SendMessage({ id, message, queue })

                const resetSeconds = response?.headers.get("X-Ratelimit-Reset")
                switch (response?.status) {
                    case 429:
                        if (resetSeconds) {
                            toast.error(`You are being rate limited. Please try again in ${resetSeconds} seconds.`)
                            break
                        }

                        toast.error(`You are being rate limited. Please try again later.`)
                        break
                }
            } catch (error) {
                console.error("failed to send message", error)
                toast.error("Failed to send message")
            }

            return messages
        }, {
            optimisticData: messages,
        })
    }

    return { data, send, ...rest }
}

export default useChat