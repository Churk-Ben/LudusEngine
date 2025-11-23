<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-6">
        <n-card embedded>
          <n-result
            status="info"
            :title="t('online.lobbyTitle')"
            :description="t('online.notOpen')"
          >
            <template #footer>
              <n-space vertical>
                <n-button @click="$router.push('/roles')">
                  {{ t("role.title") }}
                </n-button>
                <n-button @click="$router.push('/local')">
                  {{ t("local.title") }}
                </n-button>
              </n-space>
            </template>
          </n-result>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NResult, NCard, NButton, NSpace } from "naive-ui";
import { useI18n } from "vue-i18n";
const { t } = useI18n();
</script>

