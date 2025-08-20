import useSWR from 'swr'

import { GetQueue, SetQueue } from '@/features/queue/api'
import type { Queue } from '@/features/queue/types'

interface useQueueArgs {
    id: string
}

const useQueue = ({ id }: useQueueArgs) => {
    const { mutate, ...rest } = useSWR(({ id }), GetQueue)

    const update = async (newData: Queue) => {
        mutate(async () => {
            await SetQueue({ queue: newData })
            return newData
        }, {
            optimisticData: newData,
        })
    }

    return { update, refresh: () => mutate(), ...rest }
}

export default useQueue