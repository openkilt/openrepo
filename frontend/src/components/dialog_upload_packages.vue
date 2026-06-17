<!--
 Copyright 2022 by Open Kilt LLC. All rights reserved.
 This file is part of the OpenRepo Repository Management Software (OpenRepo)
 OpenRepo is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License
 version 3 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
-->

<template>

    <v-dialog max-width="700" v-model="dialog">
        <template v-slot:activator="{ props }">

            <v-btn @click="resetDialog()" variant="text" v-bind="props" icon color="primary">
                <v-icon>mdi-cloud-upload-outline</v-icon>
                <v-tooltip activator="parent" location="top">Upload Package</v-tooltip>
            </v-btn>
        </template>
        <v-card>
            <v-card-title>
            <span class="text-h5">Upload Package Files</span>
            </v-card-title>
            <v-card-text>
            <v-container>
                <v-row>
                <v-col cols="12">
                    <v-file-input :accept=FILE_TYPES[this.repo_type]
                        v-model="upload_file_list" counter multiple
                        chips show-size truncate-length="32"
                        :disabled="isUploading"></v-file-input>
                </v-col>
                </v-row>
                <v-row>
                <v-col cols="12">
                    <v-checkbox label="Overwrite duplicate package" v-model="overwrite" value="overwrite"
                        :disabled="isUploading"></v-checkbox>
                </v-col>
                </v-row>

                <v-row v-if="uploads.length > 0">
                    <v-col cols="12" class="py-0">
                        <v-list density="compact" variant="plain">
                            <v-list-item v-for="item in uploads" :key="item.file.name" class="pa-1">
                                <template #prepend>
                                    <v-icon :color="itemIconColor(item)" size="small">{{ itemIcon(item) }}</v-icon>
                                </template>

                                <v-list-item-title class="text-body-2">
                                    {{ item.file.name }}
                                    <span class="text-caption text-medium-emphasis"> &middot; {{ formatSize(item.file.size) }}</span>
                                </v-list-item-title>

                                <v-list-item-subtitle v-if="item.phase === 'uploading'">
                                    <v-progress-linear :model-value="item.progress" color="primary" height="6" rounded class="mt-1"></v-progress-linear>
                                    <div class="text-caption text-medium-emphasis mt-1">
                                        {{ formatSize(item.bytesUploaded) }} / {{ formatSize(item.bytesTotal) }}
                                        &middot; {{ item.progress }}%
                                    </div>
                                </v-list-item-subtitle>

                                <v-list-item-subtitle v-else-if="item.phase === 'processing'">
                                    <v-progress-linear indeterminate color="orange" height="6" rounded class="mt-1"></v-progress-linear>
                                    <div class="text-caption text-orange mt-1">Processing...</div>
                                </v-list-item-subtitle>

                                <v-list-item-subtitle v-else-if="item.phase === 'completed'">
                                    <v-chip size="x-small" color="success" variant="tonal" class="mt-1">Uploaded</v-chip>
                                </v-list-item-subtitle>

                                <v-list-item-subtitle v-else-if="item.phase === 'failed'">
                                    <v-chip size="x-small" color="error" variant="tonal" class="mt-1">Failed</v-chip>
                                    <div class="text-caption text-error mt-1">{{ item.error }}</div>
                                </v-list-item-subtitle>
                            </v-list-item>
                        </v-list>
                    </v-col>
                </v-row>

                <v-row v-if="isUploading">
                    <v-col cols="12" class="pt-0">
                        <div class="text-caption text-medium-emphasis">
                            {{ completedCount }} / {{ uploads.length }} files
                        </div>
                    </v-col>
                </v-row>
            </v-container>

            <v-alert v-if="dialog_error_messages && !isUploading" density="compact" type="error" class="mt-2" closible>
                {{ dialog_error_messages }}
            </v-alert>
            </v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue-darken-1" text @click="dialog = false" :disabled="isUploading">Cancel</v-btn>
            <v-btn color="blue-darken-1" text @click="uploadPackages()" :disabled="isUploading || upload_file_list.length === 0">Upload</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>


<script lang="ts">

    import RepoDataService from "../services/repo_service";
    import {logger} from '@/logger.ts'

    const SIZE_UNITS = ['B', 'KB', 'MB', 'GB'];

    export default {
        name: "add-repo",
        props: [ 'repo_uid', 'repo_type'],
        data() {
            return {
                dialog: false,
                dialog_error_messages: '',
                overwrite: false,
                isUploading: false,

                upload_file_list: [],
                uploads: [] as UploadItem[],
                FILE_TYPES: {
                    'deb': '.deb',
                    'rpm': '.rpm',
                    'generic': '*'
                },
            };
        },
        computed: {
            completedCount() {
                return this.uploads.filter(u => u.phase === 'completed' || u.phase === 'failed').length;
            }
        },
        methods: {
            resetDialog() {
                this.dialog_error_messages = '';
                this.uploads = [];
                logger.debug("Reset dialog");
            },
            formatSize(bytes: number) {
                if (!bytes || bytes === 0) return '0 B';
                const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), SIZE_UNITS.length - 1);
                const val = bytes / Math.pow(1024, i);
                return val.toFixed(i > 0 ? 1 : 0) + ' ' + SIZE_UNITS[i];
            },
            itemIcon(item: UploadItem) {
                if (item.phase === 'completed') return 'mdi-check-circle-outline';
                if (item.phase === 'failed') return 'mdi-alert-circle-outline';
                if (item.phase === 'processing') return 'mdi-loading';
                return 'mdi-file-outline';
            },
            itemIconColor(item: UploadItem) {
                if (item.phase === 'completed') return 'success';
                if (item.phase === 'failed') return 'error';
                if (item.phase === 'processing') return 'orange';
                return 'grey';
            },
            sleep(ms: number) {
                return new Promise(resolve => setTimeout(resolve, ms));
            },
            getErrorMessage(e: any) {
                if (typeof e.response != 'undefined') {
                    const data = e.response.data;
                    if (typeof data.error_message != 'undefined') return data.error_message;
                    if (typeof data.detail != 'undefined') return data.detail;
                }
                return e.message || 'Unknown error';
            },
            async pollUntilDone(item: UploadItem) {
                while (true) {
                    await this.sleep(500);
                    try {
                        const response = await RepoDataService.getUploadStatus(item.taskId!);
                        const task = response.data;
                        if (task.status === 'completed') {
                            item.phase = 'completed';
                            item.result = task.result_data;
                            return;
                        } else if (task.status === 'failed') {
                            item.phase = 'failed';
                            item.error = task.error_message || 'Processing failed';
                            return;
                        }
                    } catch (e) {
                        item.phase = 'failed';
                        item.error = this.getErrorMessage(e);
                        return;
                    }
                }
            },
            async uploadPackages() {
                logger.debug("Start async upload");
                this.dialog_error_messages = '';
                this.isUploading = true;

                this.uploads = this.upload_file_list.map((file: File) => ({
                    file,
                    phase: 'pending' as const,
                    progress: 0,
                    bytesUploaded: 0,
                    bytesTotal: file.size,
                    taskId: null as string | null,
                    error: '',
                    result: null as any,
                }));

                for (const item of this.uploads) {
                    try {
                        item.phase = 'uploading';
                        const response = await RepoDataService.upload(
                            this.repo_uid, item.file, this.overwrite,
                            (event: any) => {
                                item.progress = Math.round((event.loaded / event.total) * 100);
                                item.bytesUploaded = event.loaded;
                                item.bytesTotal = event.total;
                            }
                        );

                        item.phase = 'processing';
                        item.taskId = response.data.task_id;

                        await this.pollUntilDone(item);

                        if (item.phase === 'failed') {
                            this.dialog_error_messages += item.error + '\n';
                        }
                    } catch (e: any) {
                        item.phase = 'failed';
                        item.error = this.getErrorMessage(e);
                        this.dialog_error_messages += item.error + '\n';
                        logger.debug(e);
                    }
                }

                this.isUploading = false;

                const hasError = this.uploads.some(u => u.phase === 'failed');
                logger.debug('All uploads complete, hasError:', hasError);
                this.$emit('uploads_complete');
                if (!hasError) {
                    this.dialog = false;
                }
            },
        }
    };

    interface UploadItem {
        file: File;
        phase: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
        progress: number;
        bytesUploaded: number;
        bytesTotal: number;
        taskId: string | null;
        error: string;
        result: any;
    }

    </script>


    <style scoped>

    </style>
