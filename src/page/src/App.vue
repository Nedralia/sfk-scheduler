<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

type ScheduleRow = {
  week_start: string;
  week_number: string;
  year: string;
  name: string;
  member_number?: string;
  status?: string;
};

const rows = ref<ScheduleRow[]>([]);
const loading = ref(true);
const error = ref("");

const totalAssignments = computed(() => rows.value.length);
const uniqueMembers = computed(() => new Set(rows.value.map((row) => row.name)).size);
const firstWeek = computed(() => rows.value[0]?.week_start ?? "-");
const lastWeek = computed(() => rows.value[rows.value.length - 1]?.week_start ?? "-");

const assignmentsPerYear = computed(() => {
  const counts = new Map<string, number>();
  for (const row of rows.value) {
    const year = row.year || "Unknown";
    counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort(([left], [right]) => Number(left) - Number(right))
    .map(([year, count]) => ({ year, count }));
});

const topMembers = computed(() => {
  const counts = new Map<string, number>();
  for (const row of rows.value) {
    counts.set(row.name, (counts.get(row.name) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((left, right) => right.count - left.count || safeLocaleCompare(left.name, right.name))
    .slice(0, 8);
});

const upcomingRows = computed(() => {
  const today = new Date().toISOString().slice(0, 10);
  return rows.value.filter((row) => row.week_start >= today).slice(0, 10);
});

const maxYearCount = computed(() =>
  assignmentsPerYear.value.reduce((max, item) => Math.max(max, item.count), 1),
);

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function safeLocaleCompare(left: unknown, right: unknown): number {
  return asString(left).localeCompare(asString(right));
}

function isCompletedStatus(status: unknown): boolean {
  const normalized = asString(status).trim().toLowerCase();
  return ["completed", "done", "true", "1", "yes", "y", "checked", "check", "ok", "✓", "✔"].includes(
    normalized,
  );
}

function parseLocalDate(dateInput: string): Date | null {
  if (!dateInput) {
    return null;
  }

  // Parse as local date to avoid timezone shifts from ISO parsing.
  const parts = dateInput.split("-").map((part) => Number(part));
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) {
    return null;
  }

  const [year, month, day] = parts;
  const date = new Date(year, month - 1, day);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date;
}

function isPastDue(row: ScheduleRow): boolean {
  if (isCompletedStatus(row.status)) {
    return false;
  }

  const weekStartDate = parseLocalDate(row.week_start);
  if (!weekStartDate) {
    return false;
  }

  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now > weekStartDate;
}

function parseCsv(csvText: string): ScheduleRow[] {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    return [];
  }

  const headers = lines[0].split(",").map((header) => header.trim());
  const requiredHeaders = ["week_start", "week_number", "year", "name"];
  const hasRequiredHeaders = requiredHeaders.every((header) => headers.includes(header));
  if (!hasRequiredHeaders) {
    return [];
  }

  const parsedRows: ScheduleRow[] = [];

  for (const line of lines.slice(1)) {
    const values = line.split(",");
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    parsedRows.push({
      week_start: asString(row.week_start),
      week_number: asString(row.week_number),
      year: asString(row.year),
      name: asString(row.name),
      member_number: asString(row.member_number),
      status: asString(row.status),
    });
  }

  return parsedRows.sort((left, right) => safeLocaleCompare(left.week_start, right.week_start));
}

async function fetchScheduleData() {
  const candidates = ["/data/schedule.csv", "/schedule.csv", "/data/schedule", "/schedule"];

  for (const candidate of candidates) {
    const response = await fetch(candidate, { cache: "no-store" });
    if (!response.ok) {
      continue;
    }

    const payload = await response.text();
    const parsed = parseCsv(payload);
    if (parsed.length > 0) {
      rows.value = parsed;
      return;
    }
  }

  throw new Error("No schedule data could be loaded from /data/schedule.csv.");
}

onMounted(async () => {
  try {
    await fetchScheduleData();
  } catch (caught) {
    const message = caught instanceof Error ? caught.message : "Failed to load schedule data.";
    error.value = message;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="page">
    <section class="hero">
      <h1>SFK Cleaning Schedule</h1>
    </section>

    <section v-if="loading" class="panel">
      <p>Loading schedule...</p>
    </section>

    <section v-else-if="error" class="panel error">
      <p>{{ error }}</p>
    </section>

    <template v-else>
      <section class="stats">
        <article class="panel stat-card">
          <h2>Total Assignments</h2>
          <p>{{ totalAssignments }}</p>
        </article>
        <article class="panel stat-card">
          <h2>Unique Members</h2>
          <p>{{ uniqueMembers }}</p>
        </article>
        <article class="panel stat-card">
          <h2>First Week</h2>
          <p>{{ firstWeek }}</p>
        </article>
        <article class="panel stat-card">
          <h2>Last Week</h2>
          <p>{{ lastWeek }}</p>
        </article>
      </section>

      <section class="two-column">
        <article class="panel">
          <h2>Assignments by Year</h2>
          <div class="year-bars">
            <div v-for="item in assignmentsPerYear" :key="item.year" class="year-row">
              <span>{{ item.year }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: `${Math.max(8, (item.count / maxYearCount) * 100)}%` }"
                />
              </div>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
        </article>

        <article class="panel">
          <h2>Upcoming Weeks</h2>
          <ul class="upcoming-list">
            <li v-for="row in upcomingRows" :key="`${row.week_start}-${row.name}`">
              <span>{{ row.week_start }}</span>
              <span>W{{ row.week_number }}</span>
              <strong>{{ row.name }}</strong>
            </li>
          </ul>
        </article>
      </section>

      <section class="two-column">
        <article class="panel">
          <h2>Most Frequent Assignments</h2>
          <ol class="member-list">
            <li v-for="member in topMembers" :key="member.name">
              <span>{{ member.name }}</span>
              <strong>{{ member.count }}</strong>
            </li>
          </ol>
        </article>
      </section>

      <section class="panel">
        <h2>Full Schedule</h2>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Week Start</th>
                <th>Week Number</th>
                <th>Year</th>
                <th>Name</th>
                <th>Member #</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="`${row.week_start}-${row.name}-${row.member_number}`">
                <td>{{ row.week_start }}</td>
                <td>{{ row.week_number }}</td>
                <td>{{ row.year }}</td>
                <td>{{ row.name }}</td>
                <td>{{ row.member_number || "-" }}</td>
                <td>
                  <span v-if="isCompletedStatus(row.status)" class="status-mark status-done" aria-label="Completed"
                    >✓</span
                  >
                  <span v-else-if="isPastDue(row)" class="status-mark status-not-done" aria-label="Overdue">✗</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.status-mark {
  font-weight: 700;
}

.status-done {
  color: #1f9d55;
}

.status-not-done {
  color: #d93025;
}
</style>
