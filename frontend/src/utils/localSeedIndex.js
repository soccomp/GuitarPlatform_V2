const EMPTY_INDEX = Object.freeze({
  courses: [],
  videos: [],
  songs: [],
})

let cachedSeedIndex = null

function buildSeedIndexUrl() {
  if (typeof window === 'undefined') return ''
  if (window.location.protocol === 'file:') {
    return '../backend/data/index.json'
  }
  return '/backend/data/index.json'
}

export async function loadLocalSeedIndex() {
  if (cachedSeedIndex) return cachedSeedIndex

  const seedUrl = buildSeedIndexUrl()
  if (!seedUrl) return EMPTY_INDEX

  try {
    const response = await fetch(seedUrl, { cache: 'no-store' })
    if (!response.ok) {
      throw new Error(`Seed index request failed: ${response.status}`)
    }
    const data = await response.json()
    cachedSeedIndex = {
      courses: Array.isArray(data?.courses) ? data.courses : [],
      videos: Array.isArray(data?.videos) ? data.videos : [],
      songs: Array.isArray(data?.songs) ? data.songs : [],
    }
    return cachedSeedIndex
  } catch {
    return EMPTY_INDEX
  }
}
