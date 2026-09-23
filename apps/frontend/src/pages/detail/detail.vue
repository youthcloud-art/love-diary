<script setup lang="ts">
import {ref} from "vue";import {onLoad} from "@dcloudio/uni-app";import {request} from "../../api";const item=ref<any>();onLoad(async q=>item.value=await request(`/api/v1/entries/${q?.id}`));
</script>
<template><view v-if="item" class="page"><text class="date">{{item.happened_on}} · {{item.mood}}</text><text class="title">{{item.title||'无题'}}</text><text class="author">{{item.author_nickname}}</text><text class="body">{{item.body}}</text><image v-for="m in item.media" :key="m.id" :src="m.url" mode="widthFix"/></view></template>
<style scoped>.page{padding:40rpx}.date,.author{display:block;color:#98757a}.title{display:block;font-size:48rpx;font-weight:700;margin:20rpx 0}.body{display:block;white-space:pre-wrap;line-height:1.8;margin:40rpx 0}image{width:100%;border-radius:20rpx;margin-bottom:18rpx}</style>

