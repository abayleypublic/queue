interface APIConfig {
    api_url: string
    queue: string
}

interface Config {
    apiURL: string
    queue: string
}

let config: Config = {
    apiURL: '',
    queue: '',
}
try {
    const res = await fetch('/config.json')
    const json = await res.json() as APIConfig
    config = {
        apiURL: json.api_url,
        queue: json.queue,
    }
} catch (error) {
    console.error('error loading config:', error)
}

export default config