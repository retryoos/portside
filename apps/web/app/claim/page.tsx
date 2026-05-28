import { redirect } from "next/navigation";

// Claims are now addressed by /cases (list) and /cases/<id> (detail). Keep /claim
// as a redirect so older links do not break.
export default function ClaimRedirectPage() {
  redirect("/cases");
}
