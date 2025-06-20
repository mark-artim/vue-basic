<template>
  <v-container class="pa-4">
    <h2>Admin Dashboard</h2>

    <v-row>
      <v-col cols="12" md="6">
        <v-card @click="goTo('/admin/companies')" class="hoverable" outlined>
          <v-card-title>
            <v-icon left>mdi-domain</v-icon>
            Manage Companies
          </v-card-title>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card @click="goTo('/admin/users')" class="hoverable" outlined>
          <v-card-title>
            <v-icon left>mdi-account-group</v-icon>
            Manage Users
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const goTo = (path) => router.push(path)
</script>
