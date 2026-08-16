<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/vm">
    <domain type="kvm">
      <name><xsl:value-of select="@name"/></name>
      <memory unit="GiB"><xsl:value-of select="@ram"/></memory>
      <memoryBacking>
        <xsl:choose>
            <xsl:when test="@hardened = 'true'"><locked/></xsl:when>
            <xsl:when test="mount"><source type="memfd"/><access mode="shared"/></xsl:when>
        </xsl:choose>
      </memoryBacking>
      <vcpu><xsl:value-of select="@cpu"/></vcpu>
      <os>
        <type arch="x86_64" machine="pc-q35-10.2">hvm</type>
        <loader readonly="yes" type="pflash" stateless="yes" format="raw">/run/libvirt/nix-ovmf/edk2-x86_64-code.fd</loader>
        <xsl:choose>
          <xsl:when test="@kernel"><kernel><xsl:value-of select="@kernel"/></kernel></xsl:when>
          <xsl:otherwise><boot dev="hd"/></xsl:otherwise>
        </xsl:choose>
      </os>
      <features><acpi/><apic/><ioapic driver="kvm"/><smm state="off"/><vmport state="off"/></features>
      <cpu mode="host-passthrough" check="none" migratable="off"/>
      <clock offset="utc"/>
      <devices>
        <emulator>/run/libvirt/nix-emulators/qemu-system-x86_64</emulator>
        <xsl:if test="@disk">
          <disk type="file" device="disk">
            <driver name="qemu" type="qcow2" iommu="on"/>
            <source file="{@disk}"/>
            <target dev="vda" bus="virtio"/>
          </disk>
        </xsl:if>
        <xsl:for-each select="net">
          <interface type="user">
            <xsl:if test="@dev"><source dev="{@dev}"/></xsl:if>
            <model type="virtio"/>
            <driver iommu="on"/>
            <rom enabled="no"/>
            <backend type="passt"/>
            <xsl:for-each select="forward">
              <portForward proto="tcp"><range start="{@host}" to="{@guest}"/></portForward>
            </xsl:for-each>
          </interface>
        </xsl:for-each>
        <xsl:if test="@ui = 'true'">
          <input type="mouse" bus="ps2"/>
          <input type="keyboard" bus="ps2"/>
          <graphics type="spice" autoport="yes"><listen type="address"/><image compression="off"/><gl enable="no"/></graphics>
          <video><model type="virtio" heads="1" primary="yes"><acceleration accel3d="no"/></model></video>
        </xsl:if>
        <xsl:if test="@gpu = 'true'">
          <hostdev mode="subsystem" type="pci" managed="yes">
            <source><address domain="0x0000" bus="0x41" slot="0x00" function="0x0"/></source>
          </hostdev>
          <hostdev mode="subsystem" type="pci" managed="yes">
            <source><address domain="0x0000" bus="0x41" slot="0x00" function="0x1"/></source>
          </hostdev>
        </xsl:if>
        <audio id="1" type="none"/>
        <watchdog model="itco" action="reset"/>
        <memballoon model="none"/>
        <rng model="virtio"><driver iommu="on"/><backend model="random">/dev/urandom</backend></rng>
        <xsl:for-each select="mount">
          <filesystem type="mount">
            <driver type="virtiofs"/>
            <source dir="{@src}"/>
            <target dir="{@dst}"/>
            <xsl:if test="@readonly"><readonly/></xsl:if>
          </filesystem>
        </xsl:for-each>
      </devices>
      <xsl:if test="@hardened = 'true'">
        <launchSecurity type="sev"><policy>0x000f</policy><cbitpos>47</cbitpos><reducedPhysBits>1</reducedPhysBits></launchSecurity>
      </xsl:if>
    </domain>
  </xsl:template>
</xsl:stylesheet>