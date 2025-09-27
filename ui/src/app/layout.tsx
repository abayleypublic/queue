import type { PropsWithChildren } from "react"

import { Toaster } from "@/components/ui/sonner"
import ThemeToggle from "@/features/theme/components/toggle"

interface LayoutProps extends PropsWithChildren { }

const Layout = ({ children }: LayoutProps) => (
    <>
        <div className="min-h-screen bg-gray-100 dark:bg-gray-800 grid grid-rows-[auto_1fr_auto]">
            <div className="bg-white dark:bg-gray-900 shadow h-16 px-4 md:px-16 content-center text-xl font-bold">
                Queue
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

export default Layout
