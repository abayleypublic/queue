import { useEffect, useMemo, useState } from 'react'

import Layout from '@/app/layout'
import ThemeProvider from '@/app/provider'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Spinner } from '@/components/ui/shadcn-io/spinner'
import Config from '@/config'
import ChatGrid from '@/features/chat/components/chat-grid'
import ChatMessage from '@/features/chat/components/chat-message'
import ChatPanel from '@/features/chat/components/chat-panel'
import useChat from '@/features/chat/hooks/use-chat'
import QueueCard from '@/features/queue/components/queue-card'
import useQueue from '@/features/queue/hooks/use-queue'
import useUser from '@/features/user/hooks/use-user'

const App = () => {
  const [input, setInput] = useState("")
  const [selectedQueue, setSelectedQueue] = useState(Config.queue || "default")

  const { user, isLoading: userLoading, error: userError } = useUser()
  const { data: chat, error: chatError, send } = useChat({ id: user?.email || '' })
  const { data: queue, isLoading: queueLoading, error: queueError, refresh: refreshQueue } = useQueue({ id: selectedQueue })

  const [isOpen, setOpen] = useState(false)

  const onFocus = () => {
    setOpen(true)
  }

  const onBlur = () => {
    setOpen(false)
  }

  /**
   * This refreshes the queue whenever a new chat message is sent.
   */
  useEffect(() => {
    refreshQueue()
  }, [chat]) // eslint-disable-line react-hooks/exhaustive-deps

  const awaitingMessage: boolean = useMemo(() => {
    return !!(chat && chat.length > 0 && chat[chat.length - 1].actor === 'user')
  }, [chat])


  if (userLoading) {
    return (
      <ThemeProvider>
        <Layout>
          <div className="flex justify-center">
            <Spinner variant="ring" />
          </div>
        </Layout>
      </ThemeProvider>
    )
  }

  if (queueError || chatError || userError) {
    return (
      <div className="flex justify-center">
        <p className="text-sm text-red-500">Oopsie</p>
      </div>
    )
  }

  if (!user?.email) {
    return (
      <ThemeProvider>
        <Layout>
          <div className="flex justify-center">
            <p className="text-sm text-red-500">Unable to identify user. Please ensure you are authenticated.</p>
          </div>
        </Layout>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider>
      <Layout>
        <div className="h-full grid grid-rows-[1fr_auto] gap-y-4 mx-2 md:mx-0">
          <div className="flex flex-col gap-4 mt-2">
            <div className="flex items-center gap-2">
              <Select value={selectedQueue} onValueChange={setSelectedQueue}>
                <SelectTrigger id="queue-select" className="w-[200px]">
                  <SelectValue placeholder="Select a queue" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">default</SelectItem>
                  <SelectItem value="foo">foo</SelectItem>
                  <SelectItem value="bar">bar</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {
              queueLoading && <div className="flex justify-center"> <Spinner variant="ring" /> </div>
            }
            {
              queue && queue.entities && queue.entities.length === 0 && (
                <div className="flex justify-center">
                  <p className="text-sm text-gray-500">Nothing in the queue</p>
                </div>
              )
            }
            {
              queue && queue.entities?.map((entity, idx) => (
                <QueueCard key={idx} position={idx + 1} title={entity.name} description={`(${entity.id})`} />
              ))
            }
          </div>
          <div>
            {
              isOpen && chat && chat.length > 0 && (
                <ChatPanel>
                  <ChatGrid>
                    {chat.map((message, index) => (
                      <ChatMessage key={index} actor={message.actor} text={message.text} />
                    ))}
                  </ChatGrid>
                  {
                    awaitingMessage && <div className="flex justify-center mt-2"><Spinner variant="ring" /></div>
                  }
                </ChatPanel>
              )
            }

            <Input
              className='my-2'
              type="text"
              disabled={awaitingMessage}
              autoComplete="off"
              placeholder="Type your message here..."
              onFocus={onFocus}
              onBlur={onBlur}
              onChange={(e) => {
                setInput(e.target.value)
              }}
              value={input}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && input.trim()) {
                  send(input, selectedQueue)
                  setInput("")
                }
              }}
            />
          </div>
        </div>
      </Layout>
    </ThemeProvider >
  )
}

export default App
