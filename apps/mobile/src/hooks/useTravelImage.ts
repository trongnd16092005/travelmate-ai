import { useEffect, useMemo, useState } from 'react';
import { Image, ImageSourcePropType } from 'react-native';
import { fallbackImageForDestination } from '@/constants/design';

type WikiPage = {
  pageid?: number;
  index?: number;
  missing?: string;
  thumbnail?: { source?: string };
  original?: { source?: string };
};

type WikiResponse = {
  query?: { pages?: Record<string, WikiPage> };
};

type TravelImageState = {
  source: ImageSourcePropType;
  uri: string | null;
  loading: boolean;
};

const BLANK_IMAGE: ImageSourcePropType = { uri: '' };
const resolvedCache = new Map<string, string | null>();
const pendingCache = new Map<string, Promise<string | null>>();

function cacheKey(subject: string, context?: string) {
  return `${subject}|${context ?? ''}`
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

function imageFromResponse(payload: WikiResponse) {
  const pages = Object.values(payload.query?.pages ?? {}).sort((left, right) => (left.index ?? Number.MAX_SAFE_INTEGER) - (right.index ?? Number.MAX_SAFE_INTEGER));
  const page = pages.find((candidate) => !candidate.missing && (candidate.thumbnail?.source || candidate.original?.source));
  // Page-image thumbnails are rasterized by MediaWiki, which React Native can
  // display even when the original file is SVG/TIFF.
  return page?.thumbnail?.source ?? page?.original?.source ?? null;
}

async function queryWikipedia(language: 'vi' | 'en', subject: string, context?: string) {
  const endpoint = `https://${language}.wikipedia.org/w/api.php`;
  const common = 'action=query&format=json&origin=*&prop=pageimages&piprop=thumbnail%7Coriginal&pithumbsize=1400';
  const exactUrl = `${endpoint}?${common}&redirects=1&titles=${encodeURIComponent(subject)}`;

  const exact = await fetch(exactUrl);
  if (exact.ok) {
    const exactImage = imageFromResponse(await exact.json() as WikiResponse);
    if (exactImage) return exactImage;
  }

  const searchTerm = [subject, context].filter(Boolean).join(' ');
  const searchUrl = `${endpoint}?${common}&generator=search&gsrnamespace=0&gsrlimit=3&gsrsearch=${encodeURIComponent(searchTerm)}`;
  const search = await fetch(searchUrl);
  if (!search.ok) return null;
  return imageFromResponse(await search.json() as WikiResponse);
}

async function resolveWikipediaImage(subject: string, context?: string) {
  const key = cacheKey(subject, context);
  if (resolvedCache.has(key)) return resolvedCache.get(key) ?? null;

  const pending = pendingCache.get(key);
  if (pending) return pending;

  const request = (async () => {
    try {
      const viImage = await queryWikipedia('vi', subject, context);
      if (viImage) return viImage;
      return await queryWikipedia('en', subject, context);
    } catch {
      return null;
    }
  })();

  pendingCache.set(key, request);
  const resolved = await request;
  pendingCache.delete(key);
  resolvedCache.set(key, resolved);
  if (resolved) Image.prefetch(resolved).catch(() => undefined);
  return resolved;
}

function useWikipediaImage(subject?: string, context?: string, preferredUrl?: string | null, fallback?: ImageSourcePropType | null): TravelImageState {
  const initialSource = useMemo<ImageSourcePropType>(() => {
    if (preferredUrl) return { uri: preferredUrl };
    return fallback ?? BLANK_IMAGE;
  }, [fallback, preferredUrl]);
  const [state, setState] = useState<TravelImageState>({ source: initialSource, uri: preferredUrl ?? null, loading: Boolean(subject && !preferredUrl) });

  useEffect(() => {
    let active = true;
    if (preferredUrl) {
      setState({ source: { uri: preferredUrl }, uri: preferredUrl, loading: false });
      Image.prefetch(preferredUrl).catch(() => undefined);
      return () => { active = false; };
    }
    if (!subject?.trim()) {
      setState({ source: fallback ?? BLANK_IMAGE, uri: null, loading: false });
      return () => { active = false; };
    }

    setState({ source: fallback ?? BLANK_IMAGE, uri: null, loading: true });
    resolveWikipediaImage(subject.trim(), context).then((uri) => {
      if (!active) return;
      setState({ source: uri ? { uri } : (fallback ?? BLANK_IMAGE), uri, loading: false });
    });
    return () => { active = false; };
  }, [context, fallback, preferredUrl, subject]);

  return state;
}

export function useDestinationImage(destination?: string, preferredUrl?: string | null) {
  const fallback = fallbackImageForDestination(destination);
  return useWikipediaImage(destination, 'du lịch Việt Nam', preferredUrl, fallback);
}

export function usePlaceImage(placeName?: string, destination?: string, preferredUrl?: string | null) {
  return useWikipediaImage(placeName, destination, preferredUrl, fallbackImageForDestination(destination));
}
