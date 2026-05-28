import { redirect } from "next/navigation";

// The dashboard now lives at /cases (the voyage case list). Keep / as the entry
// point by redirecting there so bookmarks and the wordmark link still land home.
export default function HomePage() {
  redirect("/cases");
}
