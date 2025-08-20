interface APIConfig {
    api_url: string
    queue: string
    user: string
}

interface Config {
    apiURL: string
    queue: string
    user: string
}

let config: Config = {
    apiURL: '',
    queue: '',
    user: ''
}
try {
    const res = await fetch('/config.json')
    const json = await res.json() as APIConfig
    config = {
        apiURL: json.api_url,
        queue: json.queue,
        user: json.user
    }
} catch (error) {
    console.error('error loading config:', error)
}

export default config