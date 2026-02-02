"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

const locales = [
  { code: "es", label: "ES", flag: "🇪🇸" },
  { code: "en", label: "EN", flag: "🇬🇧" },
];

export function LanguageSwitcher() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleChange = (locale: string) => {
    // Set cookie and refresh
    document.cookie = `locale=${locale};path=/;max-age=31536000`;
    startTransition(() => {
      router.refresh();
    });
  };

  // Get current locale from cookie
  const getCurrentLocale = () => {
    if (typeof document === "undefined") return "es";
    const match = document.cookie.match(/locale=([^;]+)/);
    return match ? match[1] : "es";
  };

  return (
    <div className="flex items-center gap-1">
      {locales.map((locale) => (
        <button
          key={locale.code}
          onClick={() => handleChange(locale.code)}
          disabled={isPending}
          className={`px-2 py-1 text-sm rounded transition-colors ${
            getCurrentLocale() === locale.code
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
