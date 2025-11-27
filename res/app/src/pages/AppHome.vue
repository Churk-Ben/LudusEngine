<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-6">
        <n-card embedded>
          <n-result
            status="info"
            :title="t('app.title')"
            :description="t('app.description')"
          >
            <template #icon>
              <FontAwesomeIcon
                size="5x"
                class="my-1"
                :icon="faGamepad"
                :style="{ color: '#3BAAFF' }"
              />
            </template>
            <template #footer>
              <n-space vertical>
                <n-button @click="$router.push('/local')">
                  {{ t("local.title") }}
                </n-button>
                <n-button @click="$router.push('/online')" disabled>
                  {{ t("online.title") }}
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
import { useI18n } from "vue-i18n";
import { NCard, NButton, NResult, NSpace } from "naive-ui";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faGamepad } from "@fortawesome/free-solid-svg-icons";
const { t } = useI18n();
</script>
