import { Panel } from "../../components/Panel";

export function EmptyFeature({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <Panel title={title} subtitle={subtitle}>
      <div className="state">
        <p>This page is wired to the shared backend and ready for expansion.</p>
      </div>
    </Panel>
  );
}
