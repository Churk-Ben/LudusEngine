<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-6">
        <n-card embedded>
          <n-result
            status="info"
            :title="t('online.lobbyTitle')"
            :description="t('online.notOpen')"
          />
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NResult, NCard } from "naive-ui";
import { useI18n } from "vue-i18n";
const { t } = useI18n();
</script>

<style scoped>
.container {
  height: 100%;
  display: flex;
  align-items: center;
}

.row {
  width: 100%;
  display: flex;
  justify-content: center;
}
</style>
