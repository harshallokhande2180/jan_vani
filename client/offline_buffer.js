/**
 * Jan-Vani Client Offline Buffer (IndexedDB)
 * Stores recorded complaints locally if network is offline,
 * and automatically flushes/syncs when the device regains connectivity.
 * Complies with Section 3.1 & Section 5.5 of Build Plan.
 */

const DB_NAME = "JanVaniOfflineDB";
const STORE_NAME = "buffered_complaints";
const DB_VERSION = 1;

class OfflineBuffer {
  constructor() {
    this.db = null;
    this.initPromise = this.initDB();
    this.setupNetworkListeners();
  }

  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: "id" });
        }
      };
      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };
      request.onerror = (event) => {
        console.error("IndexedDB initialization error:", event.target.error);
        reject(event.target.error);
      };
    });
  }

  setupNetworkListeners() {
    window.addEventListener("online", () => {
      console.log("Device is online! Synchronizing buffered complaints...");
      this.syncAll();
    });
  }

  async saveComplaint(payload) {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], "readwrite");
      const store = tx.objectStore(STORE_NAME);
      const record = {
        id: "offline_" + Date.now() + "_" + Math.random().toString(36).substr(2, 5),
        payload: payload,
        timestamp: new Date().toISOString(),
        synced: false
      };
      const req = store.put(record);
      req.onsuccess = () => resolve(record);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async getAll() {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async remove(id) {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], "readwrite");
      const store = tx.objectStore(STORE_NAME);
      const req = store.delete(id);
      req.onsuccess = () => resolve(true);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async syncAll(apiEndpoint = "/api/submit-complaint") {
    const items = await this.getAll();
    if (!items || items.length === 0) return { count: 0 };

    let syncedCount = 0;
    for (const item of items) {
      try {
        const response = await fetch(apiEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(item.payload)
        });
        if (response.ok) {
          await this.remove(item.id);
          syncedCount++;
        }
      } catch (err) {
        console.warn("Failed to sync item:", item.id, err);
      }
    }
    return { count: syncedCount };
  }
}

window.offlineBuffer = new OfflineBuffer();
