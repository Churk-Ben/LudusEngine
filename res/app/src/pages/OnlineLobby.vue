<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-12">
        <n-result
          status="info"
          :title="t('online.lobbyTitle')"
          :description="t('online.notOpen')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NResult } from "naive-ui";
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
}
</style>
