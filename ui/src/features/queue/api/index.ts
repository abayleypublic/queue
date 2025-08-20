import Config from "@/config"
import type { Queue } from "@/features/queue/types"

interface GetQueueArgs {
    id: string
}

export const GetQueue = async ({ id }: GetQueueArgs): Promise<Queue> => {
    const response = await fetch(`${Config.apiURL}/backend/queue/${id}`)
    const data = await response.json()
    return data
}

interface SetQueueArgs {
    queue: Queue
}

export const SetQueue = async ({ queue }: SetQueueArgs) => {
    const response = await fetch(`${Config.apiURL}/backend/queues/${queue.id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(queue)
    })
    await response.json()
}