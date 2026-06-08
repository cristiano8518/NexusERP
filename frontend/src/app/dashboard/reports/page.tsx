"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ReportsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/analytics");
  }, [router]);

  return (
    <p className="text-sm text-gray-400">Аналитика & Есептер бөліміне бағытталуда...</p>
  );
}
