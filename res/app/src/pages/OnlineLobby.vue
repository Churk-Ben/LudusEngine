<template>
    <div class="container">
        <div class="row g-3">
            <div class="col-12">
                <n-card>
                    <strong>{{ t('online.lobbyTitle') }}</strong>
                    <div class="text-muted mt-2">
                        {{ t('online.notOpen') }}
                    </div>
                </n-card>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { NCard } from "naive-ui";
import { useI18n } from "vue-i18n";
const { t } = useI18n();
</script>
