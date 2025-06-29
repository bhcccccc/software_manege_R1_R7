class water:
    def __init__(self, province, location, date=None, water_temperature=None, pH=None, dissolved_oxygen=None,
                 conductivity=None,
                 turbidity=None, permanganate_index=None, ammonia_nitrogen=None, total_phosphorus=None,
                 total_nitrogen=None, site_condition=None, id=None):
        self.id = id
        self.location = location
        self.date = date
        self.water_temperature = water_temperature
        self.pH = pH
        self.dissolved_oxygen = dissolved_oxygen
        self.conductivity = conductivity
        self.turbidity = turbidity
        self.permanganate_index = permanganate_index
        self.ammonia_nitrogen = ammonia_nitrogen
        self.total_phosphorus = total_phosphorus
        self.total_nitrogen = total_nitrogen
        self.site_condition = site_condition
        self.province = province

    def str(self):
        ans = "("
        ans2 = "("
        if self.id is not None and self.id != '':
            ans += f"\'{self.id}\',"
            ans2 += "`id`,"
        ans += f"\'{self.province}\',\'{self.location}\'"
        ans2 += "`province`,`location`"
        if self.date is not None and self.date != '':
            ans += f",\'{self.date}\'"
            ans2 += ",`date`"
        if self.water_temperature is not None and self.water_temperature != '':
            ans += f",{self.water_temperature}"
            ans2 += ",`water_temperature`"
        if self.pH is not None and self.pH != '':
            ans += f",{self.pH}"
            ans2 += ",`pH`"
        if self.dissolved_oxygen is not None and self.dissolved_oxygen != '':
            ans += f",{self.dissolved_oxygen}"
            ans2 += ",`dissolved_oxygen`"
        if self.conductivity is not None and self.conductivity != '':
            ans += f",{self.conductivity}"
            ans2 += ",`conductivity`"
        if self.turbidity is not None and self.turbidity != '':
            ans += f",{self.turbidity}"
            ans2 += ",`turbidity`"
        if self.permanganate_index is not None and self.permanganate_index != '':
            ans += f",{self.permanganate_index}"
            ans2 += ",`permanganate_index`"
        if self.ammonia_nitrogen is not None and self.ammonia_nitrogen != '':
            ans += f",{self.ammonia_nitrogen}"
            ans2 += ",`ammonia_nitrogen`"
        if self.total_phosphorus is not None and self.total_phosphorus != '':
            ans += f",{self.total_phosphorus}"
            ans2 += ",`total_phosphorus`"
        if self.total_nitrogen is not None and self.total_nitrogen != '':
            ans += f",{self.total_nitrogen}"
            ans2 += ",`total_nitrogen`"
        if self.site_condition is not None and self.site_condition != '':
            ans += f",\'{self.site_condition}\'"
            ans2 += ",`site_condition`"
        ans2 += ")"
        ans += ")"
        return ans2, ans
