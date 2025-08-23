export function stamp(step: string) {
  return function(target: any, key: string, descriptor: PropertyDescriptor) {
    const orig = descriptor.value;
    descriptor.value = async function(...args: any[]) {
      // TODO: send 'start' receipt
      const out = await orig.apply(this, args);
      // TODO: send 'end' receipt
      return out;
    }
    return descriptor;
  }
}
