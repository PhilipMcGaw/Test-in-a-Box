(() => {
  'use strict';

  const fields = {
    version: 'version',
    release_stage: 'release-stage',
    repository_layout: 'repository-layout',
    bootstrap_version: 'bootstrap-version',
    updater_version: 'updater-version',
    python_version: 'python-version',
    update_channel: 'update-channel',
    update_ref: 'update-ref',
    commit: 'commit',
    updated_at: 'updated-at',
    archive_sha256: 'archive-sha256',
  };

  function displayValue(value) {
    if (value === null || value === undefined || value === '') {
      return 'unknown';
    }

    return String(value);
  }

  function setStatus(message, isError = false) {
    const status = document.getElementById('version-status');
    status.textContent = message;
    status.classList.toggle('error', isError);
  }

  async function loadVersionInformation() {
    try {
      const response = await fetch('/api/version', {
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const information = await response.json();

      for (const [property, elementId] of Object.entries(fields)) {
        const element = document.getElementById(elementId);
        element.textContent = displayValue(information[property]);
      }

      setStatus('Version information loaded from the running application.');
    } catch (error) {
      for (const elementId of Object.values(fields)) {
        document.getElementById(elementId).textContent = 'unavailable';
      }

      setStatus(
        `Could not load version information: ${error.message || error}`,
        true
      );
    }
  }

  loadVersionInformation();
})();
