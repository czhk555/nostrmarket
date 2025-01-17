async function stallList(path) {
  const template = await loadTemplateAsync(path)
  Vue.component('stall-list', {
    name: 'stall-list',
    template,

    props: [`adminkey`, 'inkey', 'wallet-options'],
    data: function () {
      return {
        filter: '',
        stalls: [],
        currencies: [],
        stallDialog: {
          show: false,
          data: {
            name: '',
            description: '',
            wallet: null,
            currency: 'sat',
            shippingZones: []
          }
        },
        zoneOptions: [],
        stallsTable: {
          columns: [
            {
              name: '',
              align: 'left',
              label: '',
              field: ''
            },
            {
              name: 'id',
              align: 'left',
              label: 'Name',
              field: 'id'
            },
            {
              name: 'currency',
              align: 'left',
              label: 'Currency',
              field: 'currency'
            },
            {
              name: 'description',
              align: 'left',
              label: 'Description',
              field: 'description'
            },
            {
              name: 'shippingZones',
              align: 'left',
              label: 'Shipping Zones',
              field: 'shippingZones'
            }
          ],
          pagination: {
            rowsPerPage: 10
          }
        }
      }
    },
    computed: {
      filteredZoneOptions: function () {
        return this.zoneOptions.filter(
          z => z.currency === this.stallDialog.data.currency
        )
      }
    },
    methods: {
      sendStallFormData: async function () {
        await this.createStall({
          name: this.stallDialog.data.name,
          wallet: this.stallDialog.data.wallet,
          currency: this.stallDialog.data.currency,
          shipping_zones: this.stallDialog.data.shippingZones,
          config: {
            description: this.stallDialog.data.description
          }
        })
      },
      createStall: async function (stall) {
        try {
          const {data} = await LNbits.api.request(
            'POST',
            '/nostrmarket/api/v1/stall',
            this.adminkey,
            stall
          )
          this.stallDialog.show = false
          data.expanded = false
          this.stalls.unshift(data)
          this.$q.notify({
            type: 'positive',
            message: 'Stall created!'
          })
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      getCurrencies: async function () {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/nostrmarket/api/v1/currencies',
            this.inkey
          )

          this.currencies = ['sat', ...data]
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      getStalls: async function () {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/nostrmarket/api/v1/stall',
            this.inkey
          )
          this.stalls = data.map(s => ({...s, expanded: false}))
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      getZones: async function () {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/nostrmarket/api/v1/zone',
            this.inkey
          )
          this.zoneOptions = data.map(z => ({
            ...z,
            label: z.name
              ? `${z.name} (${z.countries.join(', ')})`
              : z.countries.join(', ')
          }))
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      handleStallDeleted: function (stallId) {
        this.stalls = _.reject(this.stalls, function (obj) {
          return obj.id === stallId
        })
      },
      handleStallUpdated: function (stall) {
        const index = this.stalls.findIndex(r => r.id === stall.id)
        if (index !== -1) {
          stall.expanded = true
          this.stalls.splice(index, 1, stall)
        }
      },
      openCreateStallDialog: async function () {
        await this.getCurrencies()
        await this.getZones()
        if (!this.zoneOptions || !this.zoneOptions.length) {
          this.$q.notify({
            type: 'warning',
            message: 'Please create a Shipping Zone first!'
          })
          return
        }
        this.stallDialog.data = {
          name: '',
          description: '',
          wallet: null,
          currency: 'sat',
          shippingZones: []
        }
        this.stallDialog.show = true
      },
      customerSelectedForOrder: function (customerPubkey) {
        this.$emit('customer-selected-for-order', customerPubkey)
      }
    },
    created: async function () {
      await this.getStalls()
      await this.getCurrencies()
      await this.getZones()
    }
  })
}
