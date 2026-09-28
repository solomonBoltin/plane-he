/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// BINA PATCH (he): "he" added to the union. Everything else is upstream v1.4.2 verbatim.
export type TLanguage =
  | "en"
  | "fr"
  | "es"
  | "ja"
  | "zh-CN"
  | "zh-TW"
  | "ru"
  | "it"
  | "cs"
  | "sk"
  | "de"
  | "ua"
  | "pl"
  | "ko"
  | "pt-BR"
  | "id"
  | "ro"
  | "vi-VN"
  | "tr-TR"
  | "he";

export interface ILanguageOption {
  label: string;
  value: TLanguage;
}
