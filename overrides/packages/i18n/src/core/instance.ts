/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ICU from "i18next-icu";
import resourcesToBackend from "i18next-resources-to-backend";
import {
  SUPPORTED_LANGUAGES,
  FALLBACK_LANGUAGE,
  DEFAULT_LANGUAGE,
  LANGUAGE_STORAGE_KEY,
  getLanguageDirection,
} from "../constants/language";
import { NAMESPACES, DEFAULT_NAMESPACE } from "../constants/namespaces";

import type { i18n as I18nInstance } from "i18next";
import type { TLanguage } from "../types";

export const i18nInstance: I18nInstance = i18n.createInstance();

i18nInstance
  .use(ICU)
  .use(initReactI18next)
  .use(resourcesToBackend((language: string, namespace: string) => import(`../locales/${language}/${namespace}.json`)));

const initialLng =
  typeof window !== "undefined"
    ? (localStorage.getItem(LANGUAGE_STORAGE_KEY) as TLanguage | null) || DEFAULT_LANGUAGE
    : DEFAULT_LANGUAGE;

/**
 * BINA PATCH (he): apply `lang` and `dir` to the document root.
 *
 * This runs (a) at module import — before the first React render, from the STORED language, so a
 * Hebrew user never sees a left-to-right flash — and (b) again once i18next has resolved the
 * language it actually settled on (the stored code can be one this build no longer ships, and
 * i18next then falls back). Upstream hardcodes `<html lang="en">` in the app shell and never sets
 * `dir` at all.
 */
const applyDirection = (language?: string | null) => {
  if (typeof document === "undefined") return;
  const lng = language || FALLBACK_LANGUAGE;
  document.documentElement.lang = lng;
  document.documentElement.dir = getLanguageDirection(lng);
};

applyDirection(initialLng);

export const initPromise = i18nInstance
  .init({
    lng: initialLng,
    fallbackLng: FALLBACK_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGES.map((l) => l.value),
    ns: NAMESPACES,
    defaultNS: DEFAULT_NAMESPACE,
    // fallbackNS ensures all namespaces are searched for any key, so components
    // don't need to pass NAMESPACES to useTranslation (which triggers re-render cascades).
    fallbackNS: NAMESPACES.filter((ns) => ns !== DEFAULT_NAMESPACE),
    partialBundledLanguages: true,
    keySeparator: ".",
    nsSeparator: false,
    interpolation: { escapeValue: false },
    returnNull: false,
    returnEmptyString: false,
    // Pinned explicitly even though it's the default — i18next-icu intercepts the
    // format pipeline and returns raw objects regardless of this flag, so the runtime
    // guard in useTranslation is what actually prevents React crashes. Documenting
    // intent here so this isn't accidentally flipped.
    returnObjects: false,
    react: { useSuspense: false },
  })
  // Eagerly pre-load all namespaces for the initial language so they're cached
  // before any component renders. This prevents the re-render cascade that occurs
  // when react-i18next triggers concurrent async loads for unloaded namespaces.
  .then(() => i18nInstance.loadNamespaces(NAMESPACES))
  // BINA PATCH (he): re-apply after resolution — `initialLng` may be a code this build does not
  // ship, in which case i18next falls back and the direction must follow the language it chose.
  .then(() => applyDirection(i18nInstance.resolvedLanguage || initialLng));
