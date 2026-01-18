import Config from "@/config"
import { type User } from '@/features/user/types'

export const GetUser = async (): Promise<User> => {
    const response = await fetch(`${Config.apiURL}/service/user/me`)
    if (!response.ok) {
        throw new Error('Failed to fetch user data')
    }
    return await response.json()
}

export const SignOut = async (): Promise<void> => {
    window.location.href = `${Config.apiURL}/oauth2/sign_out`
}
