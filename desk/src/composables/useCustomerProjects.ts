import { createResource } from "frappe-ui";
import { computed } from "vue";
import { isCustomerPortal } from "@/utils";

export interface CustomerProject {
  customer: string;
  label: string;
}

export function useCustomerProjects() {
  const resource = createResource({
    url: "helpdesk.api.customer_team.get_projects",
    auto: isCustomerPortal.value,
  });
  const projects = computed<CustomerProject[]>(() => resource.data || []);
  const labels = computed<Record<string, string>>(() =>
    Object.fromEntries(
      projects.value.map(({ customer, label }) => [customer, label])
    )
  );
  const projectLabel = (customer: string) => labels.value[customer] || customer;

  return { projects, labels, projectLabel };
}
