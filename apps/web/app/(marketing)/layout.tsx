import type { ReactNode } from "react";
import MarketingNav from "@/components/marketing/MarketingNav";
import Footer from "@/components/marketing/Footer";

// Shared chrome for every marketing route (the landing + the meta pages).
// MarketingNav sits transparent over the hero and solidifies on scroll;
// Footer carries the sitemap and the legal links.
export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="bg-neutral text-primary">
      <MarketingNav />
      {children}
      <Footer />
    </div>
  );
}
