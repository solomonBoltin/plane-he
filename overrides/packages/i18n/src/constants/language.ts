/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import type { TLanguage, ILanguageOption } from "../types";

export const FALLBACK_LANGUAGE: TLanguage = "en";

/**
 * BINA PATCH (he): the language a user with no stored choice gets.
 *
 * Deliberately NOT `FALLBACK_LANGUAGE`, which stays "en": the fallback is what a MISSING key
 * resolves to (an untranslated string should read as English, not as a bare key), while this is
 * what the product OPENS in. On a Hebrew-only deployment, landing in English until someone finds
 * the language picker is the wrong first impression.
 */
export const DEFAULT_LANGUAGE: TLanguage = "he";

// BINA PATCH (he): Hebrew added, plus the direction machinery upstream does not have.
// Upstream ships 19 locales and NOT ONE of them is right-to-left, so "there is no RTL support
// here" is not an oversight to work around in CSS — direction has to become a property of the
// language, exactly as `lang` already is.
export const SUPPORTED_LANGUAGES: ILanguageOption[] = [
  { label: "עברית", value: "he" },
  { label: "English", value: "en" },
  { label: "Français", value: "fr" },
  { label: "Español", value: "es" },
  { label: "日本語", value: "ja" },
  { label: "简体中文", value: "zh-CN" },
  { label: "繁體中文", value: "zh-TW" },
  { label: "Русский", value: "ru" },
  { label: "Italian", value: "it" },
  { label: "Čeština", value: "cs" },
  { label: "Slovenčina", value: "sk" },
  { label: "Deutsch", value: "de" },
  { label: "Українська", value: "ua" },
  { label: "Polski", value: "pl" },
  { label: "한국어", value: "ko" },
  { label: "Português Brasil", value: "pt-BR" },
  { label: "Indonesian", value: "id" },
  { label: "Română", value: "ro" },
  { label: "Tiếng việt", value: "vi-VN" },
  { label: "Türkçe", value: "tr-TR" },
];

export const LANGUAGE_STORAGE_KEY = "userLanguage";

/**
 * BINA PATCH (he): right-to-left locales. Adding one here is the whole contract: `setLanguage`
 * and the i18n instance both read it, so a new RTL language needs no other change.
 */
export const RTL_LANGUAGES = ["he", "ar", "fa", "ur"] as const;

/** BINA PATCH (he): is this locale written right-to-left? */
export const isRTLLanguage = (language?: string | null): boolean =>
  !!language && (RTL_LANGUAGES as readonly string[]).includes(language);

/** BINA PATCH (he): the `dir` value for a locale — what the DOM and every layout depends on. */
export const getLanguageDirection = (language?: string | null): "rtl" | "ltr" =>
  isRTLLanguage(language) ? "rtl" : "ltr";
