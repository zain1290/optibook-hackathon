"""Hot-reloadable settings: edit settings.json while the bot runs, changes apply within ~1 s.

Special keys:
  "pause": true      pull all quotes and stop trading (positions stay; hedger keeps running if "hedge_when_paused")
  "flatten": true    cancel everything and close all positions once (then set it back to false)
Everything else is set on the strategy, e.g. {"edge": 2, "size": 5, "penny": false, "min_edge": 2}.
"""
import json
import os
import time

ALIASES = {"skew_per_lot": "skew", "soft_limit": "soft"}
NESTED = {"take_min_edge": ("taker", "min_edge")}
SPECIAL = {"pause", "flatten", "hedge_when_paused", "end_in_secs"}


def current_settings(strategy):
    keys = ["edge", "size", "skew", "penny", "soft", "min_edge", "unwind_edge", "max_clip", "limit"]
    out = {k: getattr(strategy, k) for k in keys if hasattr(strategy, k)}
    if hasattr(strategy, "taker"):
        out["take_min_edge"] = strategy.taker.min_edge
    out.update({"pause": False, "flatten": False, "hedge_when_paused": True})
    return out


class Settings:
    def __init__(self, path, strategy, run, check_every=1.0):
        self.path, self.strategy, self.run, self.check_every = path, strategy, run, check_every
        self.flags = {"pause": False, "flatten": False, "hedge_when_paused": True}
        self._mtime, self._last_check, self._applied = None, 0.0, {}
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(current_settings(strategy), f, indent=2)
        self.poll(force=True)

    def poll(self, force=False):
        if not force and time.monotonic() - self._last_check < self.check_every:
            return
        self._last_check = time.monotonic()
        try:
            mtime = os.path.getmtime(self.path)
            if mtime == self._mtime and not force:
                return
            self._mtime = mtime
            with open(self.path) as f:
                new = json.load(f)
        except Exception as ex:  # half-saved file etc: keep old settings
            self.run.event("settings_error", error=repr(ex))
            return
        changes, rejected = {}, {}
        for k, v in new.items():
            if self._applied.get(k) == v and not force:
                continue
            if k == "end_in_secs" and v is not None and hasattr(self.strategy, "end_time"):
                self.strategy.end_time = self.strategy.clock() + float(v)  # session ends in v seconds
            if k in SPECIAL:
                if self.flags.get(k) != v:
                    changes[k] = [self.flags.get(k), v]
                self.flags[k] = v
            elif k in NESTED and hasattr(self.strategy, NESTED[k][0]):
                obj = getattr(self.strategy, NESTED[k][0])
                old = getattr(obj, NESTED[k][1], None)
                if old != v:
                    changes[k] = [old, v]
                setattr(obj, NESTED[k][1], v)
            elif hasattr(self.strategy, ALIASES.get(k, k)):
                attr = ALIASES.get(k, k)
                old = getattr(self.strategy, attr)
                if old != v:
                    changes[k] = [old, v]
                setattr(self.strategy, attr, v)
            else:
                rejected[k] = v
            self._applied[k] = v
        if changes or rejected:
            self.run.event("settings", changes=changes, unknown_keys=rejected, file=new)
            print(f"settings applied: {changes}" + (f" unknown keys ignored: {list(rejected)}" if rejected else ""))
