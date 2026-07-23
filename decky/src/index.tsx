import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  ToggleField,
  staticClasses
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster
} from "@decky/api";
import { useEffect, useState } from "react";
import { FaDesktop } from "react-icons/fa";

type SessionMode = "desktop" | "game";

interface Status {
  session_raw: string | null;
  desired_default: SessionMode;
  matches_desired: boolean;
  autofix_enabled: boolean;
  last_action: string | null;
  last_action_time: string | null;
  last_checked_time?: string;
}

const getStatus = callable<[], Status>("get_status");
const refreshStatus = callable<[], Status>("refresh_status");
const forceFix = callable<[], Status>("force_fix");
const setDesiredDefault = callable<[mode: SessionMode], Status>("set_desired_default");
const setAutofix = callable<[enabled: boolean], Status>("set_autofix");

function Content() {
  const [status, setStatus] = useState<Status | undefined>();
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getStatus().then(setStatus).catch(console.error);

    const listener = addEventListener<[Status]>("status_update", (s) => setStatus(s));
    return () => removeEventListener("status_update", listener);
  }, []);

  const withBusy = async (action: () => Promise<Status>, toastBody: (s: Status) => string) => {
    setBusy(true);
    try {
      const result = await action();
      setStatus(result);
      toaster.toast({ title: "Force Desktop Mode", body: toastBody(result) });
    } catch (err) {
      console.error("Plugin action failed:", err);
    } finally {
      setBusy(false);
    }
  };

  const onForceDesktop = () =>
    withBusy(
      () => setDesiredDefault("desktop"),
      (s) => (s.matches_desired ? "Desktop Mode is now the default" : "Failed to set Desktop Mode, check logs")
    );

  const onReapply = () =>
    withBusy(
      () => forceFix(),
      (s) => (s.matches_desired ? "Setting reapplied successfully" : "Reapply failed, check logs")
    );

  const onRevertToGame = () =>
    withBusy(
      () => setDesiredDefault("game"),
      (s) => (s.matches_desired ? "Game Mode is now the default" : "Failed to set Game Mode, check logs")
    );

  const onToggleAutofix = async (enabled: boolean) => {
    try {
      const result = await setAutofix(enabled);
      setStatus(result);
    } catch (err) {
      console.error("Failed to toggle autofix:", err);
    }
  };

  const onRefresh = async () => {
    setBusy(true);
    try {
      const res = await refreshStatus();
      setStatus(res);
    } finally {
      setBusy(false);
    }
  };

  const statusLine = () => {
    if (!status) return "Loading status...";
    const wanted = status.desired_default === "desktop" ? "Desktop Mode" : "Game Mode";
    return status.matches_desired
      ? `✅ Default is set to ${wanted}`
      : `⚠️ Default should be ${wanted}, but currently isn't`;
  };

  return (
    <PanelSection title="Default boot session">
      <PanelSectionRow>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>{statusLine()}</span>
        </div>
      </PanelSectionRow>

      {status?.last_action && (
        <PanelSectionRow>
          <div style={{ fontSize: "12px", opacity: 0.7 }}>
            Last action: {status.last_action}
          </div>
        </PanelSectionRow>
      )}

      {status && !status.matches_desired && (
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={onReapply} disabled={busy}>
            {busy ? "Working..." : "Reapply now"}
          </ButtonItem>
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={onForceDesktop} disabled={busy || status?.desired_default === "desktop"}>
          {busy ? "Working..." : "Set Desktop Mode as default"}
        </ButtonItem>
      </PanelSectionRow>

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={onRevertToGame} disabled={busy || status?.desired_default === "game"}>
          {busy ? "Working..." : "Revert to Game Mode as default"}
        </ButtonItem>
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Auto-heal"
          description="Automatically reapply chosen default if SteamOS update resets it"
          checked={status?.autofix_enabled ?? true}
          onChange={onToggleAutofix}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ButtonItem layout="below" onClick={onRefresh} disabled={busy}>
          {busy ? "Refreshing..." : "Refresh Status"}
        </ButtonItem>
      </PanelSectionRow>

      <PanelSectionRow>
        <div style={{ fontSize: "11px", opacity: 0.6 }}>
          Uses steamosctl's own persistent default login mode, plus a logout hook so a plain
          "Log Out" from Desktop Mode returns to Game Mode instead of relaunching Desktop.
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin(() => {
  return {
    name: "Force Desktop Mode",
    titleView: <div className={staticClasses.Title}>Force Desktop Mode</div>,
    content: <Content />,
    icon: <FaDesktop />,
    onDismount() {},
  };
});

