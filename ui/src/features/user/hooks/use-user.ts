import useSWR from 'swr'

import { GetUser } from '@/features/user/api'

const useUser = () => {
    const { data, error, isLoading } = useSWR('user', GetUser)

    return {
        user: data,
        isLoading,
        error
    }
}

export default useUser
