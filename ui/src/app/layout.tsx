import type { PropsWithChildren } from "react"

import { Toaster } from "@/components/ui/sonner"
import ThemeToggle from "@/features/theme/components/toggle"
import { SignOut } from "@/features/user/api"
import useUser from "@/features/user/hooks/use-user"

interface LayoutProps extends PropsWithChildren { }

const Layout = ({ children }: LayoutProps) => {
    const { user } = useUser()

    const handleSignOut = () => {
        SignOut()
    }

    return (
        <>
            <div className="min-h-screen bg-gray-100 dark:bg-gray-800 grid grid-rows-[auto_1fr_auto]">
                <div className="bg-white dark:bg-gray-900 shadow h-16 px-4 md:px-16 flex items-center justify-between">
                    <div className="text-xl font-bold">Queue</div>
                    {user?.username && (
                        <div className="flex items-center gap-4">
                            <span className="text-sm">{user.name}</span>
                            <button
                                onClick={handleSignOut}
                                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors cursor-pointer"
                            >
                                Sign Out
                            </button>
                        </div>
                    )}
                </div>
                <div className="container mx-auto">{children}</div>
                <div className="bg-white dark:bg-gray-900 shadow h-16 px-4 md:px-16 content-center text-sm font-extralight text-right grid grid-cols-[auto_1fr_auto]">
                    <div className="inline-flex gap-2 text-left items-center ">
                        <ThemeToggle />
                    </div>
                    <div />
                    <div className="inline-flex items-center">
                        <a href="https://github.com/abayleypublic/queue" target="_blank" rel="noopener noreferrer">
                            https://github.com/abayleypublic/queue
                        </a>
                    </div>
                </div>
            </div>
            <Toaster />
        </>
    )
}

export default Layout
