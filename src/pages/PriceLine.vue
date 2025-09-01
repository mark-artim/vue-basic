<template>
  <v-container class="pa-4">
    <h1>Price Line Access</h1>

    <v-autocomplete
      v-model="selectedPriceLineId"
      v-model:search="priceLineSearch"
      :items="priceLineOptions"
      item-title="description"
      item-value="id"
      label="Price Line"
      :loading="loadingPriceLines"
      no-data-text="No Price Lines found"
      @input="onSearchPriceLine"
      @update:model-value="selectedPriceLineId"
      @focus="clearPriceLineInput"
    />
    <!-- @update:search="onSearchPriceLine" -->
    <div
      v-if="selectedPriceLine"
      class="mt-4"
    >
      <p><strong>ID:</strong> {{ selectedPriceLine.id }}</p>
      <p><strong>Description:</strong> {{ selectedPriceLine.description }}</p>

      <h3 class="mt-6">
        Limit Access by Company
      </h3>
      <v-checkbox
        v-for="company in companies"
        :key="company.name"
        v-model="companyChecks[company.name]"
        :label="company.name"
        hide-details
        @update:model-value="val => toggleCompany(company, val)"
      >
        <template #append>
          <v-icon v-if="companyChecks[company.name]">
            mdi-check
          </v-icon>
        </template>
      </v-checkbox>

      <v-btn
        class="mt-4"
        :color="hasUnsavedChanges ? 'warning' : 'primary'"
        :variant="hasUnsavedChanges ? 'elevated' : 'flat'"
        @click="save"
      >
        <v-icon v-if="hasUnsavedChanges" class="me-2">mdi-content-save-alert</v-icon>
        <v-icon v-else class="me-2">mdi-content-save</v-icon>
        {{ hasUnsavedChanges ? 'Save Changes' : 'Save' }}
      </v-btn>

      <!-- Debug Section -->
      <v-divider class="my-6" />
      <h3 class="mb-4">
        <v-icon class="me-2">mdi-bug</v-icon>
        Debug: Request Payload
      </h3>
      
      <v-btn 
        color="info" 
        variant="outlined" 
        @click="showDebugPayload = !showDebugPayload"
        class="mb-4"
      >
        <v-icon class="me-2">{{ showDebugPayload ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
        {{ showDebugPayload ? 'Hide' : 'Show' }} JSON Payload
      </v-btn>

      <v-card v-if="showDebugPayload" class="mb-4" outlined>
        <v-card-title class="bg-blue-grey-lighten-5">
          <v-icon class="me-2">mdi-code-json</v-icon>
          Exact JSON Body to be sent to API
        </v-card-title>
        <v-card-text>
          <pre class="debug-json">{{ debugPayload }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-btn 
            color="success" 
            variant="outlined" 
            @click="copyToClipboard"
            size="small"
          >
            <v-icon class="me-1">mdi-content-copy</v-icon>
            Copy JSON
          </v-btn>
        </v-card-actions>
      </v-card>

      <!-- Reference Section -->
      <v-divider class="my-6" />
      
      <h3 class="mb-4">
        <v-icon class="me-2">mdi-information-outline</v-icon>
        Access Reference
      </h3>

      <!-- All Branches Accessible -->
      <v-alert
        v-if="hasNoBranchRestrictions"
        type="success"
        variant="tonal"
        class="mb-4"
      >
        <v-icon class="me-2">mdi-check-all</v-icon>
        <strong>This Price Line is accessible to ALL branches</strong>
        <div class="text-caption mt-1">
          No branch restrictions are configured - all companies and branches can access this price line.
        </div>
      </v-alert>

      <!-- Specific Branch Restrictions -->
      <div v-else>
        <v-alert
          type="info"
          variant="tonal"
          class="mb-4"
        >
          <v-icon class="me-2">mdi-account-filter</v-icon>
          <strong>This Price Line has branch restrictions</strong>
          <div class="text-caption mt-1">
            Only specific branches can access this price line. Companies are accessible only if ALL their branches are included.
          </div>
        </v-alert>

        <!-- Company Status Grid -->
        <v-row>
          <v-col
            v-for="company in companies"
            :key="company.name"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card
              variant="outlined"
              :color="getCompanyCardColor(company.name)"
              class="h-100"
            >
              <v-card-title class="d-flex align-center">
                <v-icon
                  :color="getCompanyCardColor(company.name)"
                  class="me-2"
                >
                  {{ 
                    getCompanyCardColor(company.name) === 'success' ? 'mdi-check-circle' :
                    getCompanyCardColor(company.name) === 'warning' ? 'mdi-alert-circle' :
                    getCompanyCardColor(company.name) === 'error' ? 'mdi-close-circle' :
                    'mdi-help-circle'
                  }}
                </v-icon>
                {{ company.name }}
              </v-card-title>
              
              <v-card-text>
                <div v-if="companyStatus[company.name]?.error" class="text-error">
                  <v-icon class="me-1">mdi-alert</v-icon>
                  Error loading branch data
                </div>
                
                <div v-else-if="companyStatus[company.name]?.totalBranches === 0" class="text-warning">
                  <v-icon class="me-1">mdi-help-circle</v-icon>
                  No branches found
                </div>
                
                <div v-else>
                  <div class="mb-2">
                    <strong>Status:</strong>
                    <v-chip
                      :color="getCompanyCardColor(company.name)"
                      size="small"
                      class="ms-2"
                    >
                      {{ getCompanyStatusText(company.name) }}
                    </v-chip>
                  </div>
                  
                  <div class="mb-2">
                    <strong>Total Branches:</strong> {{ companyStatus[company.name]?.totalBranches }}
                  </div>
                  
                  <div v-if="companyStatus[company.name]?.accessibleBranches?.length" class="mb-2">
                    <strong>Accessible:</strong>
                    <v-chip-group class="mt-1">
                      <v-chip
                        v-for="branch in companyStatus[company.name]?.accessibleBranches"
                        :key="branch"
                        color="success"
                        size="small"
                        variant="outlined"
                      >
                        {{ branch }}
                      </v-chip>
                    </v-chip-group>
                  </div>
                  
                  <div v-if="companyStatus[company.name]?.missingBranches?.length">
                    <strong>Missing:</strong>
                    <v-chip-group class="mt-1">
                      <v-chip
                        v-for="branch in companyStatus[company.name]?.missingBranches"
                        :key="branch"
                        color="error"
                        size="small"
                        variant="outlined"
                      >
                        {{ branch }}
                      </v-chip>
                    </v-chip-group>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </div>
    </div>

    <!-- Save Confirmation Dialog -->
    <v-dialog v-model="showSaveConfirmDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="warning" class="me-2">mdi-content-save-alert</v-icon>
          Confirm Price Line Access Changes
        </v-card-title>
        
        <v-card-text>
          <p class="mb-4">Are you sure you want to update access for <strong>{{ selectedPriceLine?.description }}</strong>?</p>
          
          <div v-if="getChangeSummary().added.length || getChangeSummary().removed.length">
            <h4 class="mb-3">Changes to be made:</h4>
            
            <div v-if="getChangeSummary().added.length" class="mb-3">
              <v-alert type="success" variant="tonal" density="compact">
                <strong>✅ Adding access to {{ getChangeSummary().added.length }} branches:</strong>
                <div class="mt-1">
                  <v-chip
                    v-for="branchId in getChangeSummary().added"
                    :key="branchId"
                    color="success"
                    size="small"
                    class="me-1 mb-1"
                    variant="outlined"
                  >
                    {{ branchId }}
                  </v-chip>
                </div>
              </v-alert>
            </div>
            
            <div v-if="getChangeSummary().removed.length">
              <v-alert type="error" variant="tonal" density="compact">
                <strong>❌ Removing access from {{ getChangeSummary().removed.length }} branches:</strong>
                <div class="mt-1">
                  <v-chip
                    v-for="branchId in getChangeSummary().removed"
                    :key="branchId"
                    color="error"
                    size="small"
                    class="me-1 mb-1"
                    variant="outlined"
                  >
                    {{ branchId }}
                  </v-chip>
                </div>
              </v-alert>
            </div>
          </div>
          
          <v-alert type="info" variant="tonal" density="compact" class="mt-3">
            <v-icon class="me-2">mdi-information</v-icon>
            These changes will affect user access to this price line immediately.
          </v-alert>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" @click="cancelSave">Cancel</v-btn>
          <v-btn color="primary" @click="confirmSave">Save Changes</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Unsaved Changes Warning Dialog -->
    <v-dialog v-model="showUnsavedChangesDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="warning" class="me-2">mdi-alert</v-icon>
          Unsaved Changes
        </v-card-title>
        
        <v-card-text>
          <p>You have unsaved changes to the current price line access settings.</p>
          <p>What would you like to do?</p>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" @click="cancelChange">Stay Here</v-btn>
          <v-btn color="error" @click="discardChanges">Discard Changes</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useDebouncedSearch } from '@/composables/useDebouncedSearch'
import apiClient from '@/utils/axios'
import { searchPriceLines } from '@/api/priceLines'
import { getPriceLine } from '@/api/priceLines'
import { getTerritory } from '@/api/territories'

const selectedPriceLineId = ref(null)
const selectedPriceLine = ref(null)
const branchAccessList = ref([])
const originalBranchAccessList = ref([])
const companyStatus = ref({})
const showSaveConfirmDialog = ref(false)
const showUnsavedChangesDialog = ref(false)
const pendingPriceLineId = ref(null)
const showDebugPayload = ref(false)

const fetchPriceLines = async (query) => {
      const result = await searchPriceLines(query);
      const searchResults = result.results || result;
      console.log('[DEBUG PRICE LINE SEARCH] Price Lines fetched:', searchResults);
      // return allCustomers.filter(v => v.isPayTo);
      return searchResults
    };

const {
  searchTerm: priceLineSearch,
  results: priceLineOptions,
  isLoading: loadingPriceLines,
  onSearch: onSearchPriceLine,
  clear: clearPriceLines
} = useDebouncedSearch(fetchPriceLines,1000)
  // const { data } = await apiClient.get(`/PriceLines?keyword=${keyword}`)
  // return data.results || []
// }, 300)

const companies = [
  { name: 'Benoist', territoryId: 'TCBBS' },
  { name: 'Coastal', territoryId: 'TCCSC' },
  { name: "Ed's Central", territoryId: 'TCESC' },
  { name: "Ed's East", territoryId: 'TCESE' },
  { name: "Ed's West", territoryId: 'TCESW' },
  { name: 'NuComfort', territoryId: 'TCNCS' },
  { name: 'Wittichen', territoryId: 'TCWSC' }
]

const companyChecks = ref({})
companies.forEach(c => { companyChecks.value[c.name] = false })

// Computed properties for the reference section
const hasNoBranchRestrictions = computed(() => 
  !branchAccessList.value || branchAccessList.value.length === 0
)

// Change detection
const hasUnsavedChanges = computed(() => {
  if (!originalBranchAccessList.value || !branchAccessList.value) return false
  
  // Extract branch IDs for comparison
  const originalIds = originalBranchAccessList.value.map(item => 
    typeof item === 'string' ? item : (item.branchId || item.id || item.branch || item)
  ).sort()
  
  const currentIds = branchAccessList.value.map(item => 
    typeof item === 'string' ? item : (item.branchId || item.id || item.branch || item)
  ).sort()
  
  return JSON.stringify(originalIds) !== JSON.stringify(currentIds)
})

// Debug payload computed property
const debugPayload = computed(() => {
  if (!selectedPriceLine.value) return 'No price line selected'
  
  const updatedPriceLine = { ...selectedPriceLine.value }
  updatedPriceLine.branchAccessList = branchAccessList.value.map(item => 
    typeof item === 'string' ? item : (item.branchId || item.id || item.branch || item)
  )
  
  return JSON.stringify(updatedPriceLine, null, 2)
})

// Get changes for confirmation dialog
const getChangeSummary = () => {
  if (!originalBranchAccessList.value || !branchAccessList.value) return { added: [], removed: [] }
  
  const originalIds = originalBranchAccessList.value.map(item => 
    typeof item === 'string' ? item : (item.branchId || item.id || item.branch || item)
  )
  
  const currentIds = branchAccessList.value.map(item => 
    typeof item === 'string' ? item : (item.branchId || item.id || item.branch || item)
  )
  
  const added = currentIds.filter(id => !originalIds.includes(id))
  const removed = originalIds.filter(id => !currentIds.includes(id))
  
  return { added, removed }
}

// Helper function to get company card color
const getCompanyCardColor = (companyName) => {
  const status = companyStatus.value[companyName]
  if (!status) return 'grey'
  
  if (status.error || status.totalBranches === 0) return 'grey'
  if (status.accessible) return 'success'  // All branches accessible
  if (status.accessibleBranches?.length > 0) return 'warning'  // Some branches accessible
  return 'error'  // No branches accessible
}

// Helper function to get status text
const getCompanyStatusText = (companyName) => {
  const status = companyStatus.value[companyName]
  if (!status) return 'Unknown'
  
  if (status.error) return 'Error'
  if (status.totalBranches === 0) return 'No Branches'
  if (status.accessible) return 'Accessible'
  if (status.accessibleBranches?.length > 0) return 'Partial Access'
  return 'Restricted'
}

const territoryCache = {}

async function getTerritoryBranches (id) {
  if (territoryCache[id]) {
    console.log(`[DEBUG] Using cached branches for ${id}:`, territoryCache[id])
    return territoryCache[id]
  }
  
  console.log(`[DEBUG] Fetching territory data for ${id}`)
  const data = await getTerritory(id)
  console.log(`[DEBUG] Territory API response for ${id}:`, data)
  
  const branches = data.branchList || data.branches || []
  console.log(`[DEBUG] Extracted branches for ${id}:`, branches)
  
  territoryCache[id] = branches
  return branches
}

async function updateCompanyChecks () {
  console.log(`[DEBUG] Current branchAccessList:`, branchAccessList.value)
  
  // If no branch restrictions, all companies are accessible
  const hasNoBranchRestrictions = !branchAccessList.value || branchAccessList.value.length === 0
  if (hasNoBranchRestrictions) {
    console.log(`[DEBUG] No branch restrictions - all companies accessible`)
    companies.forEach(company => {
      companyChecks.value[company.name] = true
      companyStatus.value[company.name] = {
        accessible: true,
        allBranches: true,
        totalBranches: 0,
        accessibleBranches: [],
        missingBranches: []
      }
    })
    return
  }
  
  const promises = companies.map(async company => {
    try {
      const branches = await getTerritoryBranches(company.territoryId)
      
      // Fix the empty array issue - if no branches, should be false
      if (branches.length === 0) {
        companyChecks.value[company.name] = false
        companyStatus.value[company.name] = {
          accessible: false,
          allBranches: false,
          totalBranches: 0,
          accessibleBranches: [],
          missingBranches: []
        }
        console.log(`[DEBUG] Company ${company.name}: NO branches found, setting to false`)
        return
      }
      
      console.log(`[DEBUG] Checking ${company.name} branches against access list:`)
      console.log(`[DEBUG]   Territory branches: [${branches.join(', ')}]`)
      console.log(`[DEBUG]   Raw access list:`, branchAccessList.value)
      
      // Extract branch IDs from objects if needed
      const accessListBranchIds = branchAccessList.value.map(item => {
        if (typeof item === 'string') return item
        return item.branchId || item.id || item.branch || item
      })
      console.log(`[DEBUG]   Access list branch IDs: [${accessListBranchIds.join(', ')}]`)
      
      const isCompanyFullyAccessible = branches.every(b => accessListBranchIds.includes(b))
      const missingBranches = branches.filter(b => !accessListBranchIds.includes(b))
      const presentBranches = branches.filter(b => accessListBranchIds.includes(b))
      
      companyChecks.value[company.name] = isCompanyFullyAccessible
      companyStatus.value[company.name] = {
        accessible: isCompanyFullyAccessible,
        allBranches: false,
        totalBranches: branches.length,
        accessibleBranches: presentBranches,
        missingBranches: missingBranches
      }
      
      console.log(`[DEBUG]   Present branches: [${presentBranches.join(', ')}]`)
      console.log(`[DEBUG]   Missing branches: [${missingBranches.join(', ')}]`)
      console.log(`[DEBUG]   Result: all accessible = ${isCompanyFullyAccessible}`)
    } catch (err) {
      console.error('Failed to load territory', company.territoryId, err)
      companyChecks.value[company.name] = false
      companyStatus.value[company.name] = {
        accessible: false,
        allBranches: false,
        totalBranches: 0,
        accessibleBranches: [],
        missingBranches: [],
        error: true
      }
    }
  })
  
  // Actually await all the promises
  await Promise.all(promises)
}

const changePriceLine = async (id) => {
  if (!id) {
    selectedPriceLine.value = null
    branchAccessList.value = []
    originalBranchAccessList.value = []
    companies.forEach(c => { 
      companyChecks.value[c.name] = false 
      companyStatus.value[c.name] = null
    })
    return
  }
  
  console.log('[DEBUG PRICE LINE SELECTED] Fetching Price Line:', id)
  const data = await getPriceLine(id)
  console.log('[DEBUG PRICE LINE SELECTED] Price Line data:', data)
  selectedPriceLine.value = data
  branchAccessList.value = [...(data.branchAccessList || [])]
  originalBranchAccessList.value = [...(data.branchAccessList || [])]
  console.log('[DEBUG PRICE LINE SELECTED] Branch access list:', branchAccessList)
  await updateCompanyChecks()
}

watch(selectedPriceLineId, async id => {
  // Check for unsaved changes before switching
  if (hasUnsavedChanges.value && selectedPriceLine.value) {
    pendingPriceLineId.value = id
    showUnsavedChangesDialog.value = true
    return
  }
  
  await changePriceLine(id)
})

async function toggleCompany (company, checked) {
  const branches = await getTerritoryBranches(company.territoryId)
  if (checked) {
    for (const b of branches) {
      if (!branchAccessList.value.includes(b)) branchAccessList.value.push(b)
    }
  } else {
    branchAccessList.value = branchAccessList.value.filter(b => !branches.includes(b))
  }
  companyChecks.value[company.name] = checked
}

function save() {
  if (!selectedPriceLine.value) return
  if (!hasUnsavedChanges.value) {
    alert('No changes to save.')
    return
  }
  showSaveConfirmDialog.value = true
}

async function confirmSave() {
  if (!selectedPriceLine.value) return
  try {
    // Use the ERP proxy pattern like other APIs
    // Convert branch IDs to the correct object format
    const formattedBranchList = branchAccessList.value.map(item => {
      if (typeof item === 'string') {
        return { branchId: item }
      }
      return item // Already in correct format
    })
    
    // Convert Vue proxy objects to plain JavaScript objects to avoid serialization issues
    const cleanPriceLine = JSON.parse(JSON.stringify(selectedPriceLine.value))
    
    // Send the complete price line object with updated branchAccessList
    const updatedPriceLine = {
      ...cleanPriceLine,
      branchAccessList: formattedBranchList
    }
    
    // Put everything back but filter out only the truly empty entries
    // Filter out empty basisName entries from both arrays to avoid ERP errors
    if (updatedPriceLine.basisList && Array.isArray(updatedPriceLine.basisList)) {
      const originalLength = updatedPriceLine.basisList.length
      updatedPriceLine.basisList = updatedPriceLine.basisList.filter(basis => 
        basis && basis.basisName && basis.basisName.trim() !== ''
      )
      const filteredLength = updatedPriceLine.basisList.length
      if (originalLength !== filteredLength) {
        console.log(`Filtered out ${originalLength - filteredLength} empty basisName entries from basisList`)
      }
    }
    
    if (updatedPriceLine.globalBasisIds && Array.isArray(updatedPriceLine.globalBasisIds)) {
      const originalLength = updatedPriceLine.globalBasisIds.length
      updatedPriceLine.globalBasisIds = updatedPriceLine.globalBasisIds.filter(basis => 
        basis && basis.basisName && basis.basisName.trim() !== ''
      )
      const filteredLength = updatedPriceLine.globalBasisIds.length
      if (originalLength !== filteredLength) {
        console.log(`Filtered out ${originalLength - filteredLength} empty basisName entries from globalBasisIds`)
      }
    }
    
    // Eclipse limit: basisList + avgCostPriceLineBasis + lastCostPriceLineBasis cannot exceed 20
    const avgCostCount = updatedPriceLine.avgCostPriceLineBasis ? 1 : 0
    const lastCostCount = updatedPriceLine.lastCostPriceLineBasis ? 1 : 0
    const basisListLength = updatedPriceLine.basisList ? updatedPriceLine.basisList.length : 0
    const totalCount = basisListLength + avgCostCount + lastCostCount
    
    if (totalCount > 20) {
      const excessCount = totalCount - 20
      console.log(`Total basis count (${totalCount}) exceeds Eclipse limit of 20. Removing ${excessCount} basisList entries.`)
      
      if (updatedPriceLine.basisList && updatedPriceLine.basisList.length > excessCount) {
        updatedPriceLine.basisList = updatedPriceLine.basisList.slice(0, -excessCount)
        console.log(`Trimmed basisList to ${updatedPriceLine.basisList.length} entries to stay under limit`)
      }
    }
    
    // Debug the specific basis-related fields that are causing the error
    console.log('Basis-related fields:')
    console.log('- basisList length:', updatedPriceLine.basisList?.length || 0)
    console.log('- avgCostPriceLineBasis:', updatedPriceLine.avgCostPriceLineBasis)
    console.log('- lastCostPriceLineBasis:', updatedPriceLine.lastCostPriceLineBasis)
    
    // Count total basis items (the way ERP system might be counting)
    const totalBasisCount = (updatedPriceLine.basisList?.length || 0) + 
                           (updatedPriceLine.avgCostPriceLineBasis ? 1 : 0) + 
                           (updatedPriceLine.lastCostPriceLineBasis ? 1 : 0)
    console.log('Total basis count:', totalBasisCount)
    
    // Check for any duplicates or empty entries in basisList
    console.log('BasisList details:', updatedPriceLine.basisList)
    
    console.log('Sending complete price line with updated branchAccessList:', updatedPriceLine)
    
    await apiClient.post('/api/erp-proxy', {
      method: 'PUT',
      url: `/PriceLines/${selectedPriceLine.value.id}`,
      data: updatedPriceLine
    })
    
    // Update original data to reflect save
    originalBranchAccessList.value = [...branchAccessList.value]
    showSaveConfirmDialog.value = false
    
    // Show success message
    alert('Price line access updated successfully!')
  } catch (error) {
    console.error('Failed to save price line:', error)
    console.error('Error details:', error.response?.data)
    alert(`Failed to save price line: ${error.response?.data?.message || error.message}`)
  }
}

function cancelSave() {
  showSaveConfirmDialog.value = false
}

// Handle unsaved changes dialog
function discardChanges() {
  branchAccessList.value = [...originalBranchAccessList.value]
  showUnsavedChangesDialog.value = false
  selectedPriceLineId.value = pendingPriceLineId.value
}

function cancelChange() {
  showUnsavedChangesDialog.value = false
  pendingPriceLineId.value = null
  // Reset the autocomplete to the current price line
  selectedPriceLineId.value = selectedPriceLine.value?.id || null
}

// Clear price line input when focused
function clearPriceLineInput() {
  if (hasUnsavedChanges.value) {
    pendingPriceLineId.value = null
    showUnsavedChangesDialog.value = true
  } else {
    selectedPriceLineId.value = null
  }
}

// Copy debug payload to clipboard
async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(debugPayload.value)
    alert('JSON payload copied to clipboard!')
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = debugPayload.value
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    alert('JSON payload copied to clipboard!')
  }
}
</script>

<style scoped>
.debug-json {
  background-color: #f5f5f5;
  color: #333333;
  border-radius: 4px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid #e0e0e0;
  max-height: 400px;
  overflow-y: auto;
}
</style>
