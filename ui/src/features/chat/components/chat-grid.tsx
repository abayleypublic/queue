import type { PropsWithChildren } from "react"

interface ChatGridProps extends PropsWithChildren { }

const ChatGrid = ({ children }: ChatGridProps) => (
    <div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-6 h-min">
        {children}
    </div>
)


export default ChatGrid