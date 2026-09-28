/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// Components
export { TranslationProvider } from "./provider";

// Hooks
export { useTranslation } from "./hooks/use-translation";
export type { TTranslationStore } from "./hooks/use-translation";

// Types
export type { TLanguage, ILanguageOption } from "./types";
export type { TTranslationKeys } from "./types";
export type { TNamespace } from "./constants/namespaces";

// Utilities
export { setLanguage } from "./core/set-language";

// Constants
// BINA PATCH (he): the direction helpers are exported next to SUPPORTED_LANGUAGES — an app that
// renders its own language picker needs them, and re-deriving "is this RTL" per app is how the
// same list ends up in two places and drifts.
export {
  FALLBACK_LANGUAGE,
  DEFAULT_LANGUAGE,
  SUPPORTED_LANGUAGES,
  LANGUAGE_STORAGE_KEY,
  RTL_LANGUAGES,
  isRTLLanguage,
  getLanguageDirection,
} from "./constants/language";
