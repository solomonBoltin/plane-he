/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { initPromise, i18nInstance } from "./instance";
import { LANGUAGE_STORAGE_KEY, getLanguageDirection } from "../constants/language";
import type { TLanguage } from "../types";

export async function setLanguage(lng: TLanguage): Promise<void> {
  await initPromise;
  await i18nInstance.changeLanguage(lng);
  if (typeof window !== "undefined") {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lng);
    // BINA PATCH (he): upstream sets only `lang`. Without `dir` here, switching to Hebrew changes
    // every string and leaves every layout mirrored the wrong way until the next reload.
    document.documentElement.lang = lng;
    document.documentElement.dir = getLanguageDirection(lng);
  }
}
