<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-12">
        <n-card style="height: 50vh">
          <div class="d-flex align-items-center mb-2">
            <strong>{{ t("app.title") }}</strong>
          </div>
          <div class="card-text">
            {{ t("app.subtitle") }}
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { NCard, NSelect, NInput, NButton } from "naive-ui";
import { usePlayersStore } from "@/stores/players";

const players = usePlayersStore();
const { t } = useI18n();

onMounted(() => {});
</script>
