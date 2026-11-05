var base: string = import.meta.env.VITE_API_URL


const api = {
    getPicks
}


async function getPicks(handle: string) {
    const url = new URL('/api/picks', base)
    url.searchParams.set('handle', handle)
    const response = await fetch( url)
    return await response.json()
}


export default api