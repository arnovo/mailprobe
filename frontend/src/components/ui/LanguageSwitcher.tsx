"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";

const locales = [
  { code: "es", label: "ES", flag: "🇪🇸" },
  { code: "en", label: "EN", flag: "🇬🇧" },
];

const COOKIE_MAX_AGE = 31536000; // 1 year in seconds
const DEFAULT_LOCALE = "es";

function setLocaleCookie(locale: string) {
  document.cookie = `locale=${locale};path=/;max-age=${COOKIE_MAX_AGE}`;
}

function getLocaleCookie(): string {
  if (typeof document === "undefined") return DEFAULT_LOCALE;
  const match = document.cookie.match(/locale=([^;]+)/);
  return match ? match[1] : DEFAULT_LOCALE;
}

export function LanguageSwitcher() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [currentLocale, setCurrentLocale] = useState(DEFAULT_LOCALE);
  const [pendingLocale, setPendingLocale] = useState<string | null>(null);

  useEffect(() => {
    setCurrentLocale(getLocaleCookie());
  }, []);

  useEffect(() => {
    if (pendingLocale === null) return;
    setLocaleCookie(pendingLocale);
    setCurrentLocale(pendingLocale);
    startTransition(() => {
      router.refresh();
    });
    setPendingLocale(null);
  }, [pendingLocale, router]);

  const handleChange = useCallback((locale: string) => {
    setPendingLocale(locale);
  }, []);

  return (
    <div className="flex items-center gap-1">
      {locales.map((locale) => (
        <button
          key={locale.code}
          onClick={() => handleChange(locale.code)}
          disabled={isPending}
          className={`px-2 py-1 text-sm rounded transition-colors ${
            currentLocale === locale.code
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          } ${isPending ? "opacity-50 cursor-wait" : ""}`}
          title={locale.code === "es" ? "Español" : "English"}
        >
          {locale.flag} {locale.label}
        </button>
      ))}
    </div>
  );
}
