// NotingHill — store/index.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Lang } from '../i18n/translations'
import { translations } from '../i18n/translations'

interface AppState {
  theme: 'dark' | 'light'
  lang: Lang
  activeTab: string
  animationsEnabled: boolean

  // Dashboard
  dashData: any
  dashLoading: boolean

  // Search
  searchQuery: string
  searchResults: any[]
  searchLoading: boolean
  selectedItem: any | null
  searchFilters: Record<string, any>

  // Timeline
  tlZoom: 'year' | 'month' | 'day'
  tlBuckets: any[]
  tlSelectedBucket: string | null
  tlBucketItems: any[]
  tlTypeFilter: string

  // Duplicates
  dupTab: 'exact' | 'similar_text' | 'similar_image'
  dupGroups: any[]
  dupStats: any

  // Indexing
  roots: any[]
  jobs: any[]
  activeJobs: any[]
  queueSize: number

  // Virtual Folders
  vfolders: any[]
  vfSelectedId: number | null
  vfItems: any[]

  // Settings
  settings: Record<string, string>

  // Actions
  setTheme: (t: 'dark' | 'light') => void
  setLang: (l: Lang) => void
  setActiveTab: (t: string) => void
  setAnimationsEnabled: (v: boolean) => void
  setDashData: (d: any) => void
  setDashLoading: (v: boolean) => void
  setSearchQuery: (q: string) => void
  setSearchResults: (r: any[]) => void
  setSearchLoading: (v: boolean) => void
  setSelectedItem: (i: any | null) => void
  setSearchFilters: (f: Record<string, any>) => void
  setTlZoom: (z: 'year' | 'month' | 'day') => void
  setTlBuckets: (b: any[]) => void
  setTlSelectedBucket: (b: string | null) => void
  setTlBucketItems: (i: any[]) => void
  setTlTypeFilter: (t: string) => void
  setDupTab: (t: 'exact' | 'similar_text' | 'similar_image') => void
  setDupGroups: (g: any[]) => void
  setDupStats: (s: any) => void
  setVFolders: (f: any[]) => void
  setVFSelectedId: (id: number | null) => void
  setVFItems: (items: any[]) => void
  setRoots: (r: any[]) => void
  setJobs: (j: any[]) => void
  setActiveJobs: (j: any[]) => void
  setQueueSize: (n: number) => void
  setSettings: (s: Record<string, string>) => void
  t: (key: string) => string
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      lang: 'en',
      activeTab: 'dashboard',
      animationsEnabled: true,
      dashData: null,
      dashLoading: false,
      searchQuery: '',
      searchResults: [],
      searchLoading: false,
      selectedItem: null,
      searchFilters: {},
      tlZoom: 'month',
      tlBuckets: [],
      tlSelectedBucket: null,
      tlBucketItems: [],
      tlTypeFilter: '',
      dupTab: 'exact',
      dupGroups: [],
      dupStats: null,
      vfolders: [],
      vfSelectedId: null,
      vfItems: [],
      roots: [],
      jobs: [],
      activeJobs: [],
      queueSize: 0,
      settings: {},

      setTheme: (theme) => {
        set({ theme })
        document.documentElement.classList.toggle('light', theme === 'light')
      },
      setLang: (lang) => set({ lang }),
      setActiveTab: (activeTab) => set({ activeTab }),
      setAnimationsEnabled: (animationsEnabled) => {
        set({ animationsEnabled })
        document.documentElement.classList.toggle('no-animations', !animationsEnabled)
      },
      setDashData: (dashData) => set({ dashData }),
      setDashLoading: (dashLoading) => set({ dashLoading }),
      setSearchQuery: (searchQuery) => set({ searchQuery }),
      setSearchResults: (searchResults) => set({ searchResults }),
      setSearchLoading: (searchLoading) => set({ searchLoading }),
      setSelectedItem: (selectedItem) => set({ selectedItem }),
      setSearchFilters: (searchFilters) => set({ searchFilters }),
      setTlZoom: (tlZoom) => set({ tlZoom }),
      setTlBuckets: (tlBuckets) => set({ tlBuckets }),
      setTlSelectedBucket: (tlSelectedBucket) => set({ tlSelectedBucket }),
      setTlBucketItems: (tlBucketItems) => set({ tlBucketItems }),
      setTlTypeFilter: (tlTypeFilter) => set({ tlTypeFilter }),
      setDupTab: (dupTab) => set({ dupTab }),
      setDupGroups: (dupGroups) => set({ dupGroups }),
      setDupStats: (dupStats) => set({ dupStats }),
      setVFolders: (vfolders) => set({ vfolders }),
      setVFSelectedId: (vfSelectedId) => set({ vfSelectedId }),
      setVFItems: (vfItems) => set({ vfItems }),
      setRoots: (roots) => set({ roots }),
      setJobs: (jobs) => set({ jobs }),
      setActiveJobs: (activeJobs) => set({ activeJobs }),
      setQueueSize: (queueSize) => set({ queueSize }),
      setSettings: (settings) => set({ settings }),

      t: (key: string) => {
        const { lang } = get()
        const dict = translations[lang] as any
        if (!dict) return key
        const parts = key.split('.')
        let val: any = dict
        for (const p of parts) val = val?.[p]
        return typeof val === 'string' ? val : key
      },
    }),
    {
      name: 'notinghill-store',
      partialize: (s) => ({ theme: s.theme, lang: s.lang, animationsEnabled: s.animationsEnabled }),
    }
  )
)
